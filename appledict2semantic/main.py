"""
Convert Apple Dictionary HTML spans into semantic, readable HTML.
This removes the dependency on CSS styles by converting span class names into
appropriate semantic HTML tags and structural markup.
"""

import argparse
import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from appledict2semantic.helpers.io_utils import process_single_file, process_folder
from appledict2semantic.helpers.class_check import (
    find_unknown_classes_in_file,
    known_classes,
    excluded_classes,
)


def file_worker(args):
    """Worker function to find unknown classes in a single file."""
    file_path, known_classes_set, excluded_classes_set = args
    return find_unknown_classes_in_file(
        file_path, known_classes_set, excluded_classes_set
    )


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
    group.add_argument(
        "--sanity-check",
        nargs=1,
        metavar="input_folder",
        help="Check for missed classes in the HTML files. Useful for debugging or reporting issues.",
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

    if args.sanity_check:
        input_folder = args.sanity_check[0]
        html_files = []
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.lower().endswith(".html"):
                    html_files.append(os.path.join(root, file))

        args_list = [(file, known_classes, excluded_classes) for file in html_files]

        class_to_files = {}

        with Pool(processes=cpu_count()) as pool:
            # imap_unordered yields results as they complete, which works well with tqdm
            for result in tqdm(
                pool.imap_unordered(file_worker, args_list),
                total=len(args_list),
                desc="Checking classes",
            ):
                for cls, files_with_class in result.items():
                    if cls not in class_to_files:
                        class_to_files[cls] = set()
                    class_to_files[cls].update(files_with_class)
        with open("sanityresults.log", "w", encoding="utf-8") as log:
            if class_to_files:
                log.write("❗ Unknown classes list:\n")
                for cls in sorted(class_to_files):
                    log.write(f"- {cls}\n")
                log.write("\n📄 details:\n\n")
                for cls in sorted(class_to_files):
                    log.write(f"- class {cls}:\n")
                    for fname in sorted(class_to_files[cls]):
                        log.write(f"{fname}\n")
                    log.write("\n")
            else:
                log.write("No unknown classes found.\n")
        print("Sanity check complete. See sanityresults.log for details.")
        return


if __name__ == "__main__":
    main()
