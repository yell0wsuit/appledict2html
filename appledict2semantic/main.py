"""
Convert Apple Dictionary HTML spans into semantic, readable HTML.
This removes the dependency on CSS styles by converting span class names into
appropriate semantic HTML tags and structural markup.
"""

import argparse

from appledict2semantic.helpers.io_utils import process_single_file, process_folder


def main():
    """Main function to parse command line arguments and process files."""
    parser = argparse.ArgumentParser(
        description="Convert Apple Dictionary HTML to semantic HTML."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--single", nargs=2, metavar=("input", "output"), help="Process a single file."
    )
    group.add_argument(
        "--multiple",
        nargs="+",
        metavar=("input_folder", "output_folder"),
        help="Process all files in a folder.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace files in place (only with --multiple).",
    )

    args = parser.parse_args()

    if args.single:
        input_path, output_path = args.single
        process_single_file(input_path, output_path)
    elif args.multiple:
        input_folder = args.multiple[0]
        if args.replace:
            process_folder(input_folder, replace=True)
        else:
            if len(args.multiple) < 2:
                print("Error: output_folder must be specified if not using --replace.")
                return
            output_folder = args.multiple[1]
            process_folder(input_folder, output_folder=output_folder, replace=False)


if __name__ == "__main__":
    main()
