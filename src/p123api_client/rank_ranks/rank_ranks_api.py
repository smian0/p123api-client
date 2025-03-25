import logging
import os
from typing import Any

import pandas as pd

from p123api_client.common.api_client import APIClient

from .schemas import RankRanksRequest

logger = logging.getLogger(__name__)


class RankRanksError(Exception):
    """Base exception for RankRanks API errors"""

    pass


class RankRanksValidationError(RankRanksError):
    """Raised when request validation fails"""

    pass


class RankRanksAPIError(RankRanksError):
    """Raised when API request fails"""

    pass


class RankRanksAPI(APIClient):
    """API client for getting ranking system ranks"""

    @staticmethod
    def _clean_formula_name(formula: str) -> str:
        """Clean formula name to make it a valid DataFrame column name"""
        return formula.replace("(", "_").replace(")", "_").strip("_")

    def _convert_params_for_api(self, params: RankRanksRequest) -> dict[str, Any]:
        """Convert RankRanksRequest parameters to format expected by API"""
        param_dict = params.model_dump()

        # Create mapping of parameter names to match API expectations
        param_mapping = {
            "ranking_system": "rankingSystem",
            "as_of_dt": "asOfDt",
            "pit_method": "pitMethod",
            "ranking_method": "rankingMethod",
            "include_names": "includeNames",
            "include_na_cnt": "includeNaCnt",
            "include_final_stmt": "includeFinalStmt",
            "node_details": "nodeDetails",
            "tickers": "tickers",
            "currency": "currency",
            "universe": "universe",
        }

        # Convert parameter names using mapping
        converted_params = {}
        for old_name, new_name in param_mapping.items():
            if old_name in param_dict and param_dict[old_name] is not None:
                value = param_dict[old_name]
                # Convert enum values to their string representation
                if hasattr(value, "value"):
                    value = value.value
                # Convert date to string format
                if old_name == "as_of_dt":
                    value = value.strftime("%Y-%m-%d")
                converted_params[new_name] = value

        # Handle additional_data separately to ensure formulas are passed correctly
        if "additional_data" in param_dict and param_dict["additional_data"]:
            converted_params["additionalData"] = param_dict["additional_data"]

        return converted_params

    def get_ranks(self, params: RankRanksRequest, output_path: str | None = None) -> pd.DataFrame:
        """
        Get ranks for a ranking system with specified parameters and optionally save to CSV

        Args:
            params: RankRanksRequest object containing request parameters
            output_path: Optional path to save results as CSV

        Returns:
            DataFrame containing rank results

        Raises:
            RankRanksAPIError: If API request fails
        """
        try:
            logger.info(
                f"Getting ranks for ranking system: {params.ranking_system} as of {params.as_of_dt}"
            )
            logger.debug(f"Full parameters: {params.model_dump()}")

            # Convert parameters to API format
            api_params = self._convert_params_for_api(params)

            # Make API request with DataFrame conversion
            try:
                # Use make_request method from APIClient
                response = self.make_request("rank_ranks", api_params)
                logger.debug("Received rank_ranks response")

                # Convert response to DataFrame
                df = pd.DataFrame(
                    {
                        "p123_uid": response["p123Uids"],
                        "ticker": response["tickers"],
                        "rank": response["ranks"],
                    }
                )

                # Add optional columns if present
                if "names" in response:
                    df["name"] = response["names"]
                if "naCnt" in response:
                    df["na_count"] = response["naCnt"]
                if "finalStmt" in response:
                    df["final_stmt"] = response["finalStmt"]
                if "nodes" in response and "ranks" in response["nodes"]:
                    if params.node_details == "composite":
                        df["composite_rank"] = [ranks[0] for ranks in response["nodes"]["ranks"]]

                # Add additional data columns if present
                if "additionalData" in response and params.additional_data:
                    for i, formula in enumerate(params.additional_data):
                        clean_formula = self._clean_formula_name(formula)
                        df[clean_formula] = [data[i] for data in response["additionalData"]]

                # Add request parameters as columns for traceability
                df["as_of_dt"] = params.as_of_dt
                df["ranking_system"] = params.ranking_system
                df["pit_method"] = params.pit_method.value
                df["precision"] = params.precision
                df["ranking_method"] = params.ranking_method
                df["universe"] = params.universe

                # Save to CSV if output path provided
                if output_path:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    file_exists = os.path.exists(output_path)
                    df.to_csv(
                        output_path,
                        mode="a" if file_exists else "w",
                        header=not file_exists,
                        index=False,
                    )
                    logger.info(f"Saved rank results to {output_path}")

                logger.info(f"Successfully retrieved ranks for {len(df)} securities")
                return df

            except Exception as e:
                raise RankRanksAPIError(f"API request failed: {str(e)}") from e

        except Exception as e:
            logger.error(f"Error in get_ranks: {str(e)}", exc_info=True)
            raise
