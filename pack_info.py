import os
import pathlib
import re
import struct

BACKUP_DIR = "original_patches"
LAYERED_FS_DIR = "romfs"
MOD_DIR = "mods"

INFO_ENTRY_STRUCT = struct.Struct('<QQQQ256s')


class InfoEntry:
    def __init__(self, *, data=None, index=None, path: pathlib.Path = None):
        self.entry_data = data
        if data:
            self.index, _, _, _, path = INFO_ENTRY_STRUCT.unpack(data)
            self.path = pathlib.Path(LAYERED_FS_DIR, MOD_DIR, path.split(b'\0', 1)[0].decode('utf-8')[len("rom:/"):])
        else:
            self.index = index
            self.path = path
            self.size = path.stat().st_size

    def data(self):
        if self.entry_data:
            return self.entry_data
        return INFO_ENTRY_STRUCT.pack(self.index, self.size, self.size, 0,
                                      ("rom:/" + '/'.join(self.path.parts[1:])).encode('ascii'))


# Ensure dirs
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.join(LAYERED_FS_DIR, MOD_DIR), exist_ok=True)

# Detect patch version
latest_patch_num = None
latest_patch_name = None
for dir_entry in os.listdir(BACKUP_DIR):
    if os.path.isdir(os.path.join(BACKUP_DIR, dir_entry)):
        patch_dir_match = re.match(r'(patch)(\d+)$', dir_entry)
        if patch_dir_match:
            cur_patch_num = int(patch_dir_match.group(2))
            if not latest_patch_num or cur_patch_num > latest_patch_num:
                latest_patch_num = cur_patch_num
                latest_patch_name = dir_entry

if not latest_patch_num:
    print(f"Failed to find latest patch. Did you include it in {BACKUP_DIR}?")
    exit(1)

print("Using found latest:", latest_patch_name)

# Collect original entries
index_entry_map = {}
path_index_map = {}
original_info0_path = os.path.join(BACKUP_DIR, latest_patch_name, "INFO0.bin")
with open(original_info0_path, 'rb') as info0_file:
    while True:
        cur_entry_data = info0_file.read(INFO_ENTRY_STRUCT.size)
        if len(cur_entry_data) == 0:
            break
        cur_entry = InfoEntry(data=cur_entry_data)
        index_entry_map[cur_entry.index] = cur_entry
        path_index_map[cur_entry.path] = cur_entry.index

original_info2_path = os.path.join(BACKUP_DIR, latest_patch_name, "INFO2.bin")
with open(original_info2_path, 'rb') as info2_file:
    _, info1_entry_count = struct.unpack('<QQ', info2_file.read())

# Scan for mods
mod_dir_path = pathlib.Path(os.path.join(LAYERED_FS_DIR, MOD_DIR))
for cur_path in mod_dir_path.glob("**/*"):
    if cur_path.is_file():
        if cur_path in path_index_map:
            cur_index = path_index_map[cur_path]
            print(f"Replace: {cur_index} - {cur_path}")
            index_entry_map[cur_index] = InfoEntry(index=cur_index, path=cur_path)
        else:
            file_index_match = re.match(r'(\d+)', cur_path.name)
            if file_index_match:
                cur_file_index = int(file_index_match.group(1))
                if cur_file_index in index_entry_map:
                    print(f"Replace: {cur_file_index} - {cur_path}")
                else:
                    print(f"Add: {cur_file_index} - {cur_path}")
                index_entry_map[cur_file_index] = InfoEntry(index=cur_file_index, path=cur_path)
            else:
                if not cur_path.match("INFO*.bin"):
                    print("Ignored: no index detected in name or info0 -", cur_path)

# Write output
os.makedirs(os.path.join(LAYERED_FS_DIR, latest_patch_name), exist_ok=True)

with open(os.path.join(LAYERED_FS_DIR, latest_patch_name, "INFO0.bin"), 'wb') as out_info0_file:
    for info_entry in sorted(index_entry_map.items(), key=lambda item: item[0]):
        out_info0_file.write(info_entry[1].data())

with open(os.path.join(LAYERED_FS_DIR, latest_patch_name, "INFO2.bin"), 'wb') as out_info2_file:
    out_info2_file.write(struct.pack("<QQ", len(index_entry_map), info1_entry_count))
