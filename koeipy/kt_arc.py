import os
import struct

from koeipy.kt_gz import compress_kt_gz

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
