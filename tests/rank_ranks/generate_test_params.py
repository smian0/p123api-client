import os

import pandas as pd

# Define test data
test_data = {
    "ranking_system": ["ApiRankingSystem", "ApiRankingSystem", "ApiRankingSystem"],
    "as_of_dt": ["2023-01-01", "2023-02-01", "2023-03-01"],
    "universe": ["SP500", "SP500", "LargeCap-Actuals-v1.0"],
    "pit_method": ["Prelim", "Prelim", "Complete"],
    "precision": [4, 3, 4],
    "ranking_method": [2, 4, 2],
    "tickers": ["AAPL,MSFT,GOOGL", "AAPL,AMZN", "MSFT,GOOGL"],
    "include_names": [True, True, False],
    "include_na_cnt": [True, False, True],
    "include_final_stmt": [True, False, False],
    "node_details": ["factor", "composite", None],
    "currency": ["USD", "USD", "USD"],
    "additional_data": ["Close(0),mktcap", "Vol(0)", None],
}


def generate_test_params():
    """Generate test parameters CSV file"""
    # Create DataFrame
    df = pd.DataFrame(test_data)

    # Define output path
    test_input_dir = f"{os.path.dirname(__file__)}/test_input"
    os.makedirs(test_input_dir, exist_ok=True)
    output_path = os.path.join(test_input_dir, "rank_ranks_test_params.csv")

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Created rank ranks test parameters file at: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_test_params()
