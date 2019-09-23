import sys

from koeipy.kt_arc import pack_kt_arc_bin


def main():
    pack_kt_arc_bin(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
