import sys
from .main import create_input_parameter_file, join_videofile


def get_filename_list() -> list[str]:
    filenames: list[str] = []
    for i, filename in enumerate(sys.argv[2:]):
        filenames.append(filename)
    return filenames


def main():
    if len(sys.argv) < 3:
        print("Join 2 or more video files together")
        print("Usage:")
        print("    osmo-join [dest] [file1] [file2] ...")
        sys.exit(1)

    processed_dir = "./processed"

    filename_list = get_filename_list()
    output_filename = sys.argv[1]

    create_input_parameter_file(processed_dir=processed_dir, filenames=filename_list)

    join_videofile(processed_dir=processed_dir, output_filename=output_filename)

    print("All done!\n")


if __name__ == "__main__":
    main()
