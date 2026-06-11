import os
import json
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
OUTPUT_FILE = os.path.join(PROJECT_DIR, "sources.json")

def test_sources_json_exists():
    """Check that sources.json was created."""
    assert os.path.isfile(OUTPUT_FILE), f"Output file not found at {OUTPUT_FILE}"

def test_sources_json_format():
    """Read and parse sources.json to verify its structure."""
    with open(OUTPUT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse {OUTPUT_FILE} as JSON: {e}")
    
    assert isinstance(data, dict), f"Expected JSON root to be an object, got {type(data)}"
    assert "models" in data, "The 'models' key is missing from the JSON response."
    assert isinstance(data["models"], list), f"Expected 'models' to be a list, got {type(data['models'])}"
    assert "pagination" in data, "The 'pagination' key is missing from the JSON response."
    assert isinstance(data["pagination"], dict), f"Expected 'pagination' to be an object, got {type(data['pagination'])}"
