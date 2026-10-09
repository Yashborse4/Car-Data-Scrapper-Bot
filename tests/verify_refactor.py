
import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from spinny_scraper import normalize_variant, CheckpointManager, extract_attribute

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRefactor(unittest.TestCase):
    
    def test_normalize_variant_attributes(self):
        """Test that unreliable attributes are None and engine_cc is extracted."""
        mock_variant = {
            "id": 123,
            "display_name": "Test Variant",
            "attributes": [
                {"display_name": "Displacement", "value": "1199 cc"},
                {"display_name": "Mileage", "value": "18.5 kmpl"},  # Should be ignored
                {"display_name": "Max Power", "value": "88 bhp"}     # Should be ignored
            ]
        }
        
        normalized = normalize_variant(
            variant=mock_variant,
            brand_name="Honda",
            model_name="Amaze",
            model_body_type="Sedan",
            model_segment="Compact",
            make_year=2015
        )
        
        self.assertEqual(normalized["engine_cc"], "1199 cc")
        self.assertIsNone(normalized["mileage_arai"])
        self.assertIsNone(normalized["power_hp"])
        self.assertIsNone(normalized["torque_nm"])
        logger.info("Attribute extraction test passed.")

    def test_checkpoint_structure(self):
        """Test that checkpoint manager handles the new structure (discovered_models)."""
        cm = CheckpointManager()
        rows = [{"id": 1}]
        models = [{"model_id": 99, "name": "TestModel"}]
        errors = []
        phase = "fetching"
        
        # Test Save
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            with patch("json.dump") as mock_json:
                cm.save(rows, models, errors, phase)
                args, _ = mock_json.call_args
                saved_data = args[0]
                
                self.assertEqual(saved_data["phase"], "fetching")
                self.assertEqual(len(saved_data["discovered_models"]), 1)
        
        logger.info("Checkpoint structure test passed.")

if __name__ == "__main__":
    unittest.main()
