# This script is deprecated. use pack_info instead
#
# Usage: infoAdd.py [info0 file to add to] [file to add] [out dir]
# the script looks for index from the filename of "file to add"

import os, sys, struct

ENTRY_SIZE = 0x120

info0FilePath = sys.argv[1]
addFilePath = sys.argv[2]
outInfoFileDir = sys.argv[3]

info0File = open(info0FilePath, 'rb')
outInfo0File = open(os.path.join(outInfoFileDir, "INFO0.bin"), 'wb')
addFileSize = os.path.getsize(addFilePath)
addFileName = os.path.basename(addFilePath)
addFileIdx = int(addFileName.split('.')[0])

while True:
    curInfoEntry = info0File.read(ENTRY_SIZE)
    if len(curInfoEntry) == 0:
        break

    curIdx = struct.unpack('<Q', curInfoEntry[:8])[0]
    if addFileIdx == curIdx:
        break
    if addFileIdx < curIdx:
        info0File.seek(-ENTRY_SIZE, 1)
        break

    outInfo0File.write(curInfoEntry)

addFileEntry = struct.pack('<QQQQ256s', addFileIdx, addFileSize, addFileSize, 0,
    ("rom:/patch1/" + addFileName).encode('ascii'))
outInfo0File.write(addFileEntry)
outInfo0File.write(info0File.read())

with open(os.path.join(outInfoFileDir, "INFO2.bin"), 'wb') as f:
    f.write(struct.pack('<QQ', outInfo0File.tell() // ENTRY_SIZE, 1))

info0File.close()
outInfo0File.close()
