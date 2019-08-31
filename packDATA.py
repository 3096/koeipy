# Repacks DATA0/1.bin without compression (for now)
# Usage: packDATA.py [DATA0 (or idx file) path] [dir containing data] [dir for output]
# data dir content naming is [index].[extension] (extension I used is just `.idxout` from Steven's tool)

import os, sys, struct

DATA_EXTENSION = ".idxout"
INDEX_BLOCK_SIZE = 0x20

indexFilePath = sys.argv[1]
dataDir = sys.argv[2]
outDir = sys.argv[3]

indexFile = open(indexFilePath, 'rb')

outIndexFile = open(os.path.join(outDir, "DATA0.bin"), 'wb')
outDATAFile = open(os.path.join(outDir, "DATA1.bin"), 'wb')

curIdx = 0
curOutOffset = 0
while (True):
	curIdxBlock = indexFile.read(INDEX_BLOCK_SIZE)
	if len(curIdxBlock) == 0:
		break

	curOffset, curSize, curSizeCompressed, curFileType = struct.unpack('<QQQQ', curIdxBlock)

	if curSize != 0:
		curDataPath = os.path.join(dataDir, str(curIdx) + DATA_EXTENSION)
		newSize = os.path.getsize(curDataPath)
		if curSize != newSize:
			print(f"index {curIdx} new size: {hex(newSize)}")
			curSize = newSize

		with open(curDataPath, 'rb') as dataFile:
			outDATAFile.write(dataFile.read())
			
		curOutOffset += curSize

	outIndexFile.write(struct.pack('<QQQQ', curOutOffset, curSize, curSize, 0))
	curIdx += 1

indexFile.close()
outIndexFile.close()
outDATAFile.close()
