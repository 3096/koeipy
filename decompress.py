import sys

from koeipy.kt_gz import decompress_kt_gz_file


def main():
    decompress_kt_gz_file(sys.argv[1], sys.argv[1][:-3])


if __name__ == "__main__":
    main()
