# Quick and dirty find then inject data
# Usage: injectFile.py [file of inject target] [file of original data] [file of modified data]

import sys

targetFilePath = sys.argv[1]
originalDataPath = sys.argv[2]
modifiedDataPath = sys.argv[3]

targetFile = open(targetFilePath, 'r+b')
originalData = open(originalDataPath, 'rb')
modifiedData = open(modifiedDataPath, 'rb')

targetFileData = targetFile.read()
offset = targetFileData.find(originalData.read())
if offset == -1:
    print("Data not found")
else:
    targetFile.seek(offset)
    targetFile.write(modifiedData.read())
    print("Data injected at ", hex(offset))

targetFile.close()
originalData.close()
modifiedData.close()
