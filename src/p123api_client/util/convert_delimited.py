"""Convert delimited files module."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def convert_delimited(input_file: str, output_file: str | None = None) -> str:
    """Convert between delimited file formats (CSV, TSV).

    Args:
        input_file: Path to input file
        output_file: Optional path to output file. If not provided,
            will use input path with new extension.

    Returns:
        Path to output file
    """
    # Get input format from extension
    in_format = Path(input_file).suffix.lower()[1:]
    if in_format not in ["csv", "tsv"]:
        raise ValueError(f"Unsupported input format: {in_format}")

    # Determine output format and file
    if not output_file:
        out_format = "tsv" if in_format == "csv" else "csv"
        output_file = str(Path(input_file).with_suffix(f".{out_format}"))
    else:
        out_format = Path(output_file).suffix.lower()[1:]
        if out_format not in ["csv", "tsv"]:
            raise ValueError(f"Unsupported output format: {out_format}")

    # Convert file
    with open(input_file) as f_in, open(output_file, "w") as f_out:
        for line in f_in:
            if in_format == "csv":
                # Convert CSV to TSV
                line = line.replace('","', "\t")
                line = line.replace(',"', "\t")
                line = line.replace('",', "\t")
                line = line.replace('"', "")
            else:
                # Convert TSV to CSV
                line = line.replace("\t", '","')
                line = f'"{line.strip()}"\n'
            f_out.write(line)

    # Log success
    base_output = os.path.basename(output_file)
    print(f"Converted {input_file} ({in_format}) to {base_output} ({out_format})")

    return output_file


def convert_delimited_to_dict(file_path: str, delimiter: str = "\t") -> None:
    """Convert a delimited file to a dict format.

    Args:
        file_path: Path to the delimited file
        delimiter: Delimiter used in the file (default: tab)
    """
    with open(file_path) as f:
        lines = f.readlines()

    headers = lines[0].strip().split(delimiter)
    data: dict[str, list[str]] = {}

    for line in lines[1:]:
        values = line.strip().split(delimiter)
        if len(values) != len(headers):
            continue

        for header, value in zip(headers, values, strict=True):
            if header not in data:
                data[header] = []
            data[header].append(value)

    with open(file_path + ".json", "w") as f:
        json.dump(data, f)


def main() -> None:
    """Run the converter from command line."""
    parser = argparse.ArgumentParser(description="Convert between CSV and TSV")
    parser.add_argument("input_file", help="Input file path")
    parser.add_argument(
        "-o", "--output", help="Output file path (optional)", default=None
    )
    args = parser.parse_args()

    try:
        convert_delimited(args.input_file, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
