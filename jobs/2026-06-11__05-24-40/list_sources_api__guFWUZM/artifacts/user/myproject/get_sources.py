import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

def fetch_sources():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable is not set.")
        return []

    base_url = "https://api.hookdeck.com/sources"
    source_names = []
    next_cursor = None

    while True:
        url = base_url
        if next_cursor:
            url += f"?next={urllib.parse.quote(next_cursor)}"

        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        retries = 3
        success = False
        while retries > 0:
            try:
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        
                        models = data.get("models", [])
                        for model in models:
                            name = model.get("name")
                            if name is not None:
                                source_names.append(name)
                        
                        pagination = data.get("pagination", {})
                        next_cursor = pagination.get("next")
                        success = True
                        break
                    else:
                        print(f"API returned unexpected status code: {response.status}")
                        retries -= 1
                        time.sleep(1)
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after else 2.0
                    print(f"Rate limited (429). Waiting for {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    print(f"HTTP Error {e.code}: {e.reason}")
                    retries -= 1
                    time.sleep(1)
            except Exception as e:
                print(f"Error during request: {e}")
                retries -= 1
                time.sleep(1)
        
        if not success:
            print("Failed to retrieve sources after retries.")
            break
        
        if not next_cursor:
            break

    return source_names

def main():
    names = fetch_sources()
    output_path = "/home/user/myproject/sources.txt"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for name in names:
            f.write(f"{name}\n")
            
    print(f"Successfully wrote {len(names)} sources to {output_path}")

if __name__ == "__main__":
    main()
