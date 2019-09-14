import os
import struct
import sys
import zlib
from typing import BinaryIO

KT_GZ_BLOCK_SIZE = 0x10000
KT_GZ_HEADER_STRUCT = struct.Struct("<III")


def compress_kt_gz(in_stream: BinaryIO, out_stream: BinaryIO, total_size, level=-1):
    def align_0x80(offset):
        return (offset + 0x7F) & ~0x7F

    base_offset = out_stream.tell()
    block_count = (total_size - 1) // KT_GZ_BLOCK_SIZE + 1
    current_offset = align_0x80(KT_GZ_HEADER_STRUCT.size + block_count * 4)
    block_sizes = bytearray()

    def write_block(in_block_size):
        compressed_block_data = zlib.compress(in_stream.read(in_block_size), level)
        block_size = len(compressed_block_data)

        out_stream.seek(base_offset + current_offset)
        out_stream.write(struct.pack("<I", block_size))
        out_stream.write(compressed_block_data)

        block_size += 4  # include the 4-byte size header
        block_sizes.extend(struct.pack("<I", block_size))
        return align_0x80(current_offset + block_size)

    for _ in range(block_count - 1):
        current_offset = write_block(KT_GZ_BLOCK_SIZE)

    # last block and pad 0
    current_offset = write_block(total_size - KT_GZ_BLOCK_SIZE * (block_count - 1))
    out_stream.write(b'\x00' * (current_offset - (out_stream.tell() - base_offset)))

    # write header
    out_stream.seek(base_offset)
    out_stream.write(KT_GZ_HEADER_STRUCT.pack(KT_GZ_BLOCK_SIZE, block_count, total_size))
    out_stream.write(block_sizes)

    out_stream.seek(base_offset + current_offset)
    return current_offset


def compress_kt_gz_file(in_path, out_path, level=-1):
    with open(in_path, 'rb') as in_file, open(out_path, 'wb') as out_file:
        compress_kt_gz(in_file, out_file, os.path.getsize(in_path), level)


KT_ARC_ENTRY_STRUCT = struct.Struct("<II")


def pack_kt_arc_bin(in_dir, out_file_path, compress_lvl=0):
    file_path_list = [os.path.join(in_dir, path) for path in os.listdir(in_dir) if not os.path.isfile(path)]
    entry_count = len(file_path_list)

    # sort by file name number, ensure order
    sorted_file_path_list = [''] * entry_count
    for file_path in file_path_list:
        file_idx = int(os.path.basename(file_path).split('.')[0])
        sorted_file_path_list[file_idx] = file_path

    out_file = open(out_file_path, 'wb')
    entries = bytearray()
    cur_offset = 4 + KT_ARC_ENTRY_STRUCT.size * entry_count
    out_file.seek(cur_offset)
    for file_path in sorted_file_path_list:
        with open(file_path, 'rb') as in_file:
            if compress_lvl:  # branch prediction OK
                write_size = compress_kt_gz(in_file, out_file, os.path.getsize(file_path), compress_lvl)
            else:
                write_size = out_file.write(in_file.read())
            entries.extend(KT_ARC_ENTRY_STRUCT.pack(cur_offset, write_size))
            cur_offset += write_size

    # write header
    out_file.seek(0)
    out_file.write(struct.pack("<I", entry_count))
    out_file.write(entries)

    out_file.close()


# test
pack_kt_arc_bin(sys.argv[1], sys.argv[2], compress_lvl=sys.argv[3])
