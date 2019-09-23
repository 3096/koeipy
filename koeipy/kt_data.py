import os
import struct

from koeipy.kt_gz import KT_GZ_EXTENSION, decompress_kt_gz

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
