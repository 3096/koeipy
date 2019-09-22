import os
import struct
import zlib
from typing import BinaryIO

# KT GZ
KT_GZ_BLOCK_SIZE = 0x10000
KT_GZ_HEADER_STRUCT = struct.Struct("<iII")
KT_GZ_EXTENSION = ".gz"


def align_0x80(offset):
    return (offset + 0x7F) & ~0x7F


def compress_kt_gz(in_stream: BinaryIO, out_stream: BinaryIO, total_size, level=-1):
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

        block_size += 4  # include the 4-byte size in block header
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


def decompress_kt_gz(in_stream: BinaryIO, out_stream: BinaryIO):
    base_offset = in_stream.tell()

    # read header
    block_size, block_count, total_size = KT_GZ_HEADER_STRUCT.unpack(in_stream.read(KT_GZ_HEADER_STRUCT.size))
    if block_size == -1:  # block has no size header
        raise NotImplementedError  # doesn't exist in Three Houses, so ¯\_(ツ)_/¯
    block_sizes = [struct.unpack('<I', in_stream.read(4))[0] for _ in range(block_count)]
    current_offset = align_0x80(KT_GZ_HEADER_STRUCT.size + block_count * 4)

    # deflate blocks
    def write_block():
        in_stream.seek(base_offset + current_offset)
        cur_block_data_size = struct.unpack('<I', in_stream.read(4))[0]
        out_stream.write(zlib.decompress(in_stream.read(cur_block_data_size)))
        return align_0x80(current_offset + cur_block_size)

    for cur_block_size in block_sizes[:-1]:
        current_offset = write_block()

    # For some reason last block can be not compressed. I have no idea how KT determines when to do this
    # Seems to happen randomly when the size is small. Only way is to check
    last_block_size = block_sizes[block_count - 1]
    if last_block_size == total_size - block_size * (block_count - 1):
        in_stream.seek(base_offset + current_offset)
        out_stream.write(in_stream.read(last_block_size))  # not compressed
        current_offset += align_0x80(last_block_size)
    else:
        current_offset = write_block()

    return current_offset


def compress_kt_gz_file(in_path, out_path, level=-1):
    with open(in_path, 'rb') as in_file, open(out_path, 'wb') as out_file:
        compress_kt_gz(in_file, out_file, os.path.getsize(in_path), level)


# KT ARC
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


# LINKDATA
DATA_INDEX_NAME = "DATA0.bin"
DATA_FILE_NAME = "DATA1.bin"
DATA_INDEX_STRUCT = struct.Struct("<QQQQ")
DATA_OUT_EXTENSION = ".idxout"


def get_file_by_index(index, data_dir=".", out_dir=".", deflate=True):
    with open(os.path.join(data_dir, DATA_INDEX_NAME), 'rb') as index_file:
        index_file.seek(index * DATA_INDEX_STRUCT.size)
        offset, uncompressed_size, linkdata_size, is_compressed = DATA_INDEX_STRUCT.unpack(
            index_file.read(DATA_INDEX_STRUCT.size))

    print(uncompressed_size, linkdata_size)

    out_extension = DATA_OUT_EXTENSION + KT_GZ_EXTENSION if is_compressed and not deflate else DATA_OUT_EXTENSION
    need_deflate = is_compressed and deflate
    with open(os.path.join(data_dir, DATA_FILE_NAME), 'rb') as data_file:
        with open(os.path.join(out_dir, str(index) + out_extension), 'wb') as out_file:
            data_file.seek(offset)
            if need_deflate:
                decompress_kt_gz(data_file, out_file)
            else:
                out_file.write(data_file.read(linkdata_size))
