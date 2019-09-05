# creates a dictionary of {index: file path} of INFO0

import struct

def getPathDict(infoPath):
    with open(infoPath, 'rb') as f:
        file = f.read()

    retDict = {}
    seeking = 0
    while seeking < len(file):
        retDict[struct.unpack('<q', file[seeking:seeking+8])[0]] = file[seeking+0x20:seeking+0x120].decode("utf-8")
        seeking += 0x120

    return retDict

def main():
    pathDict = getPathDict("example/INFO0.bin")

    for key in pathDict:
        print(f"{key} - {pathDict[key]}")

if __name__== "__main__":
    main()
