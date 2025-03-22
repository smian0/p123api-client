import os

import pandas as pd


def remove_duplicates(input_file: str) -> None:
    """
    Remove duplicate rows from TSV file based on factor_hash and rank_performance_hash

    Args:
        input_file: Path to input TSV file. Output will be saved as input_file_deduped.tsv
    """
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct absolute path for input file
    input_path = os.path.join(script_dir, input_file)

    # Verify input file is TSV
    if not input_file.endswith(".tsv"):
        raise ValueError("Input file must be a .tsv file")

    # Generate output filename by adding _deduped before .tsv
    base_name = input_file[:-4]  # remove .tsv
    output_file = f"{base_name}_deduped.tsv"
    output_path = os.path.join(script_dir, output_file)

    # Read TSV file
    df = pd.read_csv(input_path, sep="\t")

    # Count total rows before deduplication
    total_rows = len(df)

    # Check for duplicates before removal
    duplicates = df[df.duplicated(subset=["factor_hash", "rank_performance_hash"], keep=False)]
    if not duplicates.empty:
        print("\nFound duplicate rows:")
        print(duplicates[["factor_hash", "rank_performance_hash", "factor", "description"]])
        print("\nTotal duplicate rows found:", len(duplicates))

    # Remove duplicates based on factor_hash and rank_performance_hash
    df_deduplicated = df.drop_duplicates(subset=["factor_hash", "rank_performance_hash"])

    # Count duplicates removed
    duplicates_removed = total_rows - len(df_deduplicated)

    # Save deduplicated data
    df_deduplicated.to_csv(output_path, sep="\t", index=False)

    print("\nSummary:")
    print(f"Total rows processed: {total_rows}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Rows after deduplication: {len(df_deduplicated)}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates.py input.tsv")
        sys.exit(1)

    remove_duplicates(sys.argv[1])
