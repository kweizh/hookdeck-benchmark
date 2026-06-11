#!/usr/bin/env python3
import os
import sys
import json
import subprocess

def run_command(cmd):
    """Runs a command and returns its stdout, raising an exception on failure."""
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout.strip()

def get_existing_source(name):
    """Checks if a source with the given name exists and returns its ID, or None."""
    try:
        output = run_command(["hookdeck", "gateway", "source", "list", "--name", name, "--output", "json"])
        if not output:
            return None
        sources = json.loads(output)
        # The list command might return a list of sources.
        if isinstance(sources, list):
            for src in sources:
                if src.get("name") == name:
                    return src.get("id")
        elif isinstance(sources, dict):
            # If it returns a single dict instead of a list (or a wrapper object, let's check)
            if sources.get("name") == name:
                return sources.get("id")
            # If it's a paginated object with a "models" or "data" field
            for key in ["models", "data", "sources"]:
                if key in sources and isinstance(sources[key], list):
                    for src in sources[key]:
                        if src.get("name") == name:
                            return src.get("id")
        return None
    except Exception as e:
        print(f"Warning: failed to check existing source: {e}")
        return None

def get_existing_destination(name):
    """Checks if a destination with the given name exists and returns its ID, or None."""
    try:
        output = run_command(["hookdeck", "gateway", "destination", "list", "--name", name, "--output", "json"])
        if not output:
            return None
        destinations = json.loads(output)
        if isinstance(destinations, list):
            for dest in destinations:
                if dest.get("name") == name:
                    return dest.get("id")
        elif isinstance(destinations, dict):
            if destinations.get("name") == name:
                return destinations.get("id")
            for key in ["models", "data", "destinations"]:
                if key in destinations and isinstance(destinations[key], list):
                    for dest in destinations[key]:
                        if dest.get("name") == name:
                            return dest.get("id")
        return None
    except Exception as e:
        print(f"Warning: failed to check existing destination: {e}")
        return None

def get_existing_connection(name):
    """Checks if a connection with the given name exists and returns its ID, or None."""
    try:
        output = run_command(["hookdeck", "gateway", "connection", "list", "--name", name, "--output", "json"])
        if not output:
            return None
        connections = json.loads(output)
        if isinstance(connections, list):
            for conn in connections:
                if conn.get("name") == name:
                    return conn.get("id")
        elif isinstance(connections, dict):
            if connections.get("name") == name:
                return connections.get("id")
            for key in ["models", "data", "connections"]:
                if key in connections and isinstance(connections[key], list):
                    for conn in connections[key]:
                        if conn.get("name") == name:
                            return conn.get("id")
        return None
    except Exception as e:
        print(f"Warning: failed to check existing connection: {e}")
        return None

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set.")
        sys.exit(1)

    print(f"Using ZEALT_RUN_ID: {run_id}")

    source_name = f"shopify-source-{run_id}"
    destination_name = f"http-destination-{run_id}"
    destination_url = f"https://mock.hookdeck.com/{run_id}"
    connection_name = f"shopify-to-http-{run_id}"

    # 1. Create or get Shopify Source
    source_id = get_existing_source(source_name)
    if source_id:
        print(f"Found existing source: {source_name} ({source_id})")
    else:
        print(f"Creating source: {source_name}")
        output = run_command([
            "hookdeck", "gateway", "source", "create",
            "--name", source_name,
            "--type", "SHOPIFY",
            "--output", "json"
        ])
        source_data = json.loads(output)
        source_id = source_data["id"]
        print(f"Created source ID: {source_id}")

    # 2. Create or get HTTP Destination
    destination_id = get_existing_destination(destination_name)
    if destination_id:
        print(f"Found existing destination: {destination_name} ({destination_id})")
    else:
        print(f"Creating destination: {destination_name}")
        output = run_command([
            "hookdeck", "gateway", "destination", "create",
            "--name", destination_name,
            "--type", "HTTP",
            "--url", destination_url,
            "--output", "json"
        ])
        dest_data = json.loads(output)
        destination_id = dest_data["id"]
        print(f"Created destination ID: {destination_id}")

    # 3. Create or get Connection
    connection_id = get_existing_connection(connection_name)
    if connection_id:
        print(f"Found existing connection: {connection_name} ({connection_id})")
    else:
        print(f"Creating connection: {connection_name}")
        output = run_command([
            "hookdeck", "gateway", "connection", "create",
            "--name", connection_name,
            "--source-id", source_id,
            "--destination-id", destination_id,
            "--output", "json"
        ])
        conn_data = json.loads(output)
        connection_id = conn_data["id"]
        print(f"Created connection ID: {connection_id}")

    # 4. Write the Connection ID to log file
    log_dir = "/home/user/hookdeck-task"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "output.log")
    
    with open(log_path, "w") as f:
        f.write(f"Connection ID: {connection_id}\n")
    
    print(f"Successfully wrote Connection ID to {log_path}")

if __name__ == "__main__":
    main()
