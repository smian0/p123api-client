import logging

from p123api_client.common.api_client import APIClient
from p123api_client.models.schemas import RankUpdateRequest, RankUpdateResponse

logger = logging.getLogger(__name__)


class RankUpdateAPI(APIClient):
    """API client for updating ranking systems"""

    def __init__(self, api_id: str, api_key: str):
        """Initialize the API client

        Args:
            api_id: Portfolio123 API ID
            api_key: Portfolio123 API key
        """
        super().__init__(api_id=api_id, api_key=api_key)
        logger.info("Initialized RankUpdateAPI")

    def update_rank(self, rank_request: str | RankUpdateRequest) -> RankUpdateResponse:
        """Update ranking system with provided content

        Args:
            rank_request: Either an XML string or a RankUpdateRequest object

        Returns:
            RankUpdateResponse: Response from the API
        """
        logger.debug(f"Updating ranking system with content: {rank_request}")

        try:
            if isinstance(rank_request, str):
                # Already XML string input
                xml_content = rank_request
            else:
                # Convert RankUpdateRequest to XML
                xml_content = rank_request.to_xml()
                logger.debug(f"Generated XML content:\n{xml_content}")

            # Always pass XML content in 'nodes' parameter
            params = {
                "nodes": xml_content,
                "type": "stock",  # Required parameter according to docs
            }

            response = self.make_request("rank_update", params)
            logger.info(f"Response from rank_update: {response}")
            return RankUpdateResponse(status="success", message="Rank updated successfully.")

        except Exception as e:
            logger.error(f"Error updating rank: {str(e)}")
            raise
