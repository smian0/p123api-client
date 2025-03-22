import logging
import os
import unittest

import pytest

from p123api_client.common.settings import Settings
from p123api_client.models.schemas import Factor
from p123api_client.rank_update import RankType, RankUpdateAPI, RankUpdateRequest, Scope

logger = logging.getLogger(__name__)


class TestRankUpdateAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        settings = Settings(testing=True)
        cls.api_id = settings.api_id
        cls.api_key = settings.api_key

        if not cls.api_id or not cls.api_key:
            raise ValueError("API credentials not properly loaded from environment")

    @pytest.mark.vcr(cassette_name="test_update_rank_from_xml.yaml")
    def test_update_rank_from_xml(self) -> None:
        """Test rank update from XML file."""
        logger.info("Starting test_update_rank_from_xml")

        rank_update_api = RankUpdateAPI(api_id=self.api_id, api_key=self.api_key)
        xml_file_path = (
            f"{os.path.dirname(__file__)}/test_input/ranking_system_core_combination_v2.xml"
        )
        with open(xml_file_path) as xml_file:
            xml_content = xml_file.read()

        logger.debug(f"Loading XML content from: {xml_file_path}")
        response = rank_update_api.update_rank(xml_content)

        self.assertEqual(response.status, "success")

    @pytest.mark.vcr(cassette_name="test_update_rank_from_single_factor.yaml")
    def test_update_rank_from_single_factor(self) -> None:
        """Test rank update from single factor.

        VCR.py will record a new interaction if the request doesn't match
        any existing recorded interactions in the cassette.
        """
        rank_update_api = RankUpdateAPI(api_id=self.api_id, api_key=self.api_key)
        rank_update_request = RankUpdateRequest(
            factors=[
                Factor(
                    rank_type=RankType.HIGHER,
                    formula="Close(0)",
                    description="Sample details for rank update",
                )
            ],
            scope=Scope.UNIVERSE,
            description="Sample details for rank update",
        )
        xml_content = rank_update_request.to_xml()
        response = rank_update_api.update_rank(xml_content)

        self.assertEqual(response.status, "success")
        self.assertIn("Rank updated successfully.", response.message)
