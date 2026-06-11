import requests
import json

url = "https://api.hookdeck.com/2025-07-01/openapi"
resp = requests.get(url)
schema = resp.json()

print("Keys in OpenAPI:", list(schema.keys()))

# Let's inspect paths
paths = schema.get("paths", {})
print("\nPaths related to sources, destinations, connections:")
for path in paths:
    if any(x in path for x in ["source", "destination", "connection"]):
        print(path, list(paths[path].keys()))

# Let's write the schema to a file so we can read/search it easily
with open("/home/user/hookdeck-fanout/openapi.json", "w") as f:
    json.dump(schema, f, indent=2)
