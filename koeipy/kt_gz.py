import os
import struct
import zlib
from typing import BinaryIO

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
