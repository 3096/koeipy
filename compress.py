import sys

from koeipy.kt_gz import compress_kt_gz_file


def main():
    compress_kt_gz_file(sys.argv[1], sys.argv[1]+".gz", int(sys.argv[2]))


if __name__ == "__main__":
    main()
