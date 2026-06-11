import json

with open("/home/user/hookdeck-fanout/openapi.json") as f:
    schema = json.load(f)

schemas = schema.get("components", {}).get("schemas", {})
event_schema = schemas.get("Event", {})

print("Event Schema properties:")
for prop, val in event_schema.get("properties", {}).items():
    print(f"  - {prop}: {val.get('type')} / {val.get('$ref')}")
