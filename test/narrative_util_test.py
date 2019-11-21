import unittest
import requests
import requests_mock
from StaticNarrative.narrative.narrative_util import (
    read_narrative,
    _validate_nar_type
)
from StaticNarrative.narrative_ref import NarrativeRef


class NarrativeUtilTestCase(unittest.TestCase):
    def test_read_narrative_ok(self):
        pass

    def test_read_narrative_no_ref(self):
        pass

    def test_read_narrative_bad_client(self):
        pass

    def test_read_narrative_not_narrative(self):
        pass

    def test_validate_nar_type(self):
        good_types = [
            "KBaseNarrative.Narrative-1.0",
            "KBaseNarrative.Narrative-4.0"
        ]
        bad_types = [
            "SomeObject.Name",
            "kbasenarrative.Narrative-1.0"
            "KBaseNarrative.Narrative-1.0.0"
        ]
        invalid_types = [
            5,
            str,
            {"lol": "no"},
            ["wat"],
            None
        ]
        ref = NarrativeRef.parse("1/2/3")
        for t in good_types:
            self.assertIsNone(_validate_nar_type(t, ref))
        for t in bad_types:
            with self.assertRaises(ValueError) as e:
                _validate_nar_type(t, ref)
            self.assertIn(f"Expected a Narrative object with reference {str(ref)}, got a",
                          str(e.exception))
        for t in invalid_types:
            with self.assertRaises(ValueError) as e:
                _validate_nar_type(t, ref)
            self.assertIn(f"The type string must be a string",
                          str(e.exception))
