import os
import subprocess
import json

def test_connection_configured_correctly():
    """Verify that the Hookdeck connection is configured with Basic Auth on the source."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    conn_name = f"auth-conn-{run_id}"
    source_name = f"auth-source-{run_id}"
    expected_password = f"secret-password-{run_id}"

    result = subprocess.run(
        ["hookdeck", "gateway", "connection", "get", conn_name, "--include-source-auth", "--output", "json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"'hookdeck gateway connection get' failed: {result.stderr}"
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"Output is not valid JSON: {result.stdout}"

    source = data.get("source")
    assert source is not None, "JSON output does not contain a 'source' object."
    
    assert source.get("name") == source_name, f"Expected source name '{source_name}', got '{source.get('name')}'"
    
    config = source.get("config", {})
    assert config.get("auth_type") == "BASIC_AUTH", f"Expected source.config.auth_type to be 'BASIC_AUTH', got '{config.get('auth_type')}'"
    
    auth = config.get("auth", {})
    assert auth.get("username") == "admin", f"Expected username 'admin', got '{auth.get('username')}'"
    assert auth.get("password") == expected_password, f"Expected password '{expected_password}', got '{auth.get('password')}'"
