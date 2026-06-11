import os
import json
import urllib.request
import urllib.error

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set.")
        return

    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable is not set.")
        return

    source_name = f"secure-source-{run_id}"
    url = "https://api.hookdeck.com/2025-07-01/sources"
    
    payload = {
        "name": source_name,
        "type": "WEBHOOK",
        "config": {
            "auth_type": "HMAC",
            "auth": {
                "algorithm": "sha256",
                "encoding": "base64",
                "header_key": "x-custom-signature",
                "webhook_secret_key": "my_super_secret_key"
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            source_id = data.get("id")
            if not source_id:
                print("Error: 'id' not found in response.")
                print(res_body)
                return
            
            print(f"Successfully created source. ID: {source_id}")
            
            log_dir = "/home/user/hookdeck-task"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "output.log")
            with open(log_path, "w") as f:
                f.write(f"Source ID: {source_id}\n")
            print(f"Saved Source ID to {log_path}")

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
