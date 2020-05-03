# Repacks DATA0/1.bin without compression (for now)
# Usage: packDATA.py [DATA0 (or idx file) path] [dir containing data] [dir for output]
# data dir content naming is [index].bin (you can change it to `.idxout` for Steven's tool if you want)

import os
import struct
import sys

INDEX_FILE_NAME = "DATA0.bin"
DATA_FILE_NAME = "DATA1.bin"
DATA_EXTENSION = ".bin"

INDEX_BLOCK_STRUCT = struct.Struct('<QQQQ')

if __name__ == "__main__":
    index_file_path = sys.argv[1]
    data_dir = sys.argv[2]
    out_dir = sys.argv[3]

    source_index_file = open(index_file_path, 'rb')

    out_index_file = open(os.path.join(out_dir, INDEX_FILE_NAME), 'wb')
    out_data_file = open(os.path.join(out_dir, DATA_FILE_NAME), 'wb')

    cur_idx = 0
    cur_out_offset = 0
    while True:
        cur_idx_block = source_index_file.read(INDEX_BLOCK_STRUCT.size)
        if len(cur_idx_block) == 0:
            break

        cur_offset, cur_size, cur_size_compressed, cur_compression_type = INDEX_BLOCK_STRUCT.unpack(cur_idx_block)

        if cur_size != 0:
            cur_data_path = os.path.join(data_dir, str(cur_idx) + DATA_EXTENSION)
            new_size = os.path.getsize(cur_data_path)
            if cur_size != new_size:
                print(f"index {cur_idx} new size: {hex(new_size)}")
                cur_size = new_size

            with open(cur_data_path, 'rb') as dataFile:
                out_data_file.write(dataFile.read())

        out_index_file.write(struct.pack('<QQQQ', cur_out_offset, cur_size, cur_size, 0))
        cur_out_offset += cur_size
        cur_idx += 1

    source_index_file.close()
    out_index_file.close()
    out_data_file.close()
