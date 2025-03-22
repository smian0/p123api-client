import csv
import os
import xml.etree.ElementTree as ET
from pathlib import Path


def detect_format(file_path: Path) -> str:
    """Detect the format of a file based on its extension and content."""
    # Read first 1KB to check content
    with open(file_path) as f:
        content = f.read(1024)

    # Get extension
    ext = file_path.suffix.lower()

    # First check extension
    if ext == '.xml':
        return 'xml'
    elif ext == '.tsv':
        return 'tsv'

    # If no clear extension, try to detect from content
    if content.strip().startswith('<?xml'):
        return 'xml'
    elif '\t' in content:
        return 'tsv'

    raise ValueError(f'Could not detect format of file: {file_path}')


def get_output_filename(input_path: str, detected_format: str) -> str:
    """Generate output filename with _converted prefix"""
    path = Path(input_path)
    new_ext = ".tsv" if detected_format == "xml" else ".xml"
    return str(path.parent / f"{path.stem}_converted{new_ext}")


def xml_to_tsv(tree: ET.ElementTree) -> list[dict[str, str]]:
    """Convert XML tree to TSV format."""
    root = tree.getroot()
    rows = []

    for rank in root.findall('.//Rank'):
        row: dict[str, str] = {}
        for attr in rank.attrib:
            value = rank.get(attr)
            if value is not None:
                row[attr] = str(value)
        rows.append(row)

    return rows


def tsv_to_xml(rows: list[dict[str, str]]) -> ET.ElementTree:
    """Convert TSV data to XML format."""
    root = ET.Element('RankingSystem')
    ranks = ET.SubElement(root, 'Ranks')

    for row in rows:
        rank = ET.SubElement(ranks, 'Rank')
        for key, value in row.items():
            rank.set(key, value)

    return ET.ElementTree(root)


def convert_file(input_path: str) -> None:
    """Main conversion function with format detection"""
    try:
        # Get script directory and construct full path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_input_path = os.path.join(script_dir, input_path)

        # Detect format and generate output path
        detected_format = detect_format(Path(full_input_path))
        output_path = get_output_filename(full_input_path, detected_format)

        # Perform conversion
        if detected_format == "xml":
            tree = ET.parse(full_input_path)
            rows = xml_to_tsv(tree)
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=rows[0].keys(),
                    delimiter="\t",
                )
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(full_input_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)
            tree = tsv_to_xml(rows)
            ET.indent(tree, space="    ")
            tree.write(output_path, encoding="utf-8", xml_declaration=True)

        print(f"Successfully converted {full_input_path} to {output_path}")

    except Exception as e:
        print(f"Error converting file: {str(e)}")
        print(f"Tried to find file at: {os.path.abspath(full_input_path)}")
        print(f"Script directory: {script_dir}")
        raise


def main() -> None:
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Convert between XML and TSV ranking formats")
    parser.add_argument("input_file", help="Input file path (XML or TSV)")

    args = parser.parse_args()
    convert_file(args.input_file)


if __name__ == "__main__":
    main()
