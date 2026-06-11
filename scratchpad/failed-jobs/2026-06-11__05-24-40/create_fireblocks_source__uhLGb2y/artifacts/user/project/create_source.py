import os
import sys
import json
import urllib.request
import urllib.error

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable not set")
        sys.exit(1)

    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable not set")
        sys.exit(1)

    source_name = f"fireblocks-source-{run_id}"
    print(f"Target source name: {source_name}")

    # Payload for Hookdeck Source creation
    # Let's try lowercase "sandbox" first as specified in:
    # "The source must be configured with `config.auth.environment` set to `sandbox`."
    payload = {
        "name": source_name,
        "type": "FIREBLOCKS",
        "config": {
            "auth_type": "FIREBLOCKS",
            "auth": {
                "environment": "sandbox"
            }
        }
    }

    url = "https://api.hookdeck.com/2025-07-01/sources"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/7.68.0"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            print("Successfully created source with 'sandbox':")
            print(json.dumps(data, indent=2))
            source_id = data.get("id")
            if source_id:
                write_log(source_id)
                return
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"Failed with 'sandbox' (HTTP {e.code}): {err_body}")
        
        # If it failed, let's try uppercase "SANDBOX"
        print("Retrying with uppercase 'SANDBOX'...")
        payload["config"]["auth"]["environment"] = "SANDBOX"
        req2 = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req2) as response:
                res_body = response.read().decode("utf-8")
                data = json.loads(res_body)
                print("Successfully created source with 'SANDBOX':")
                print(json.dumps(data, indent=2))
                source_id = data.get("id")
                if source_id:
                    write_log(source_id)
                    return
        except urllib.error.HTTPError as e2:
            err_body2 = e2.read().decode("utf-8")
            print(f"Failed with 'SANDBOX' (HTTP {e2.code}): {err_body2}")
            sys.exit(1)

def write_log(source_id):
    log_path = "/home/user/project/source.log"
    with open(log_path, "w") as f:
        f.write(f"Source ID: {source_id}\n")
    print(f"Saved Source ID: {source_id} to {log_path}")

if __name__ == "__main__":
    main()
