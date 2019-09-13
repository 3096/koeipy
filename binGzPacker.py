import os
import struct
import sys
import zlib
from typing import BinaryIO

KT_GZ_BLOCK_SIZE = 0x10000


def compress_kt_gz(in_stream: BinaryIO, out_stream: BinaryIO, total_size, level=-1):
    def align_0x80(offset):
        return (offset + 0x7F) & ~0x7F

    base_offset = out_stream.tell()
    block_count = (total_size - 1) // KT_GZ_BLOCK_SIZE + 1
    current_offset = align_0x80(4 + block_count * 4)
    block_sizes = []

    def write_block(in_block_size):
        compressed_block_data = zlib.compress(in_stream.read(in_block_size), level)
        block_size = len(compressed_block_data)

        out_stream.seek(base_offset + current_offset)
        out_stream.write(struct.pack("<I", block_size))
        out_stream.write(compressed_block_data)

        block_size += 4
        block_sizes.append(block_size)
        return align_0x80(current_offset + block_size)

    for i in range(0, block_count - 1):
        current_offset = write_block(KT_GZ_BLOCK_SIZE)

    current_offset = write_block(total_size - KT_GZ_BLOCK_SIZE * (block_count - 1))
    out_stream.write(b'\x00' * (current_offset - (out_stream.tell() - base_offset)))

    out_stream.seek(base_offset)
    out_stream.write(struct.pack("<III", KT_GZ_BLOCK_SIZE, block_count, total_size))
    for size in block_sizes:
        out_stream.write(struct.pack("<I", size))

    out_stream.seek(base_offset + current_offset)
    return current_offset


# test
compress_kt_gz(open(sys.argv[1], "rb"), open(sys.argv[2], "wb"), os.path.getsize(sys.argv[1]), 9)
