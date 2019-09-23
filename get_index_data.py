import sys

from koeipy.kt_data import get_file_by_index


def main():
    get_file_by_index(int(sys.argv[1]), sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
