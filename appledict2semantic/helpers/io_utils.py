"""Helpers for file and folder processing, including multiprocessing and user confirmation."""

import os
import traceback
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from .process_html import process_html


def process_single_file(input_path, output_path):
    """Process a single HTML file and write the output."""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            html = f.read()
        html_out = process_html(html)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"{input_path} -> {output_path} ✅ done")
        return True
    except Exception:
        print(f"{input_path} -> {output_path} ❌ error")
        print(traceback.format_exc())
        return False


def _process_file_worker(args):
    input_path, output_path = args
    process_single_file(input_path, output_path)


def process_folder(input_folder, output_folder=None, replace=False):
    """Process all .html files in a folder (excluding _processed), with multiprocessing and tqdm."""
    files = [
        f
        for f in os.listdir(input_folder)
        if f.endswith(".html") and not f.endswith("_processed.html")
    ]
    if not files:
        print("No HTML files found to process.")
        return

    if replace:
        # Confirm with user
        print(
            "WARNING: THIS WILL REPLACE ALL OF THE FILES. THIS ACTION IS IRREVERSIBLE."
        )
        confirm = input("CONTINUE? (Y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    tasks = []
    for fname in files:
        input_path = os.path.join(input_folder, fname)
        if replace:
            output_path = input_path
        else:
            if output_folder is None:
                raise ValueError(
                    "output_folder must be specified if not replacing in place."
                )
            os.makedirs(output_folder, exist_ok=True)
            base, ext = os.path.splitext(fname)
            output_path = os.path.join(output_folder, f"{base}_processed{ext}")
        tasks.append((input_path, output_path))

    with Pool(cpu_count()) as pool:
        results = list(
            tqdm(
                pool.imap_unordered(_process_file_worker, tasks),
                total=len(tasks),
                desc="Processing files",
            )
        )

    for (input_path, output_path), success in zip(tasks, results):
        if success:
            print(f"{input_path} -> {output_path} ✅ done")
        else:
            print(f"{input_path} -> {output_path} ❌ error")
