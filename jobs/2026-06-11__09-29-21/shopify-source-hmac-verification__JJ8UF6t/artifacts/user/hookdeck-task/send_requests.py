import hmac
import hashlib
import base64
import json
import urllib.request
import os

secret = os.environ["SHOPIFY_WEBHOOK_SECRET"]
source_url = "https://hkdk.events/hoil433hzhilbl"

# Canonical JSON body - must use exact same bytes for both requests
body = json.dumps({"test": "shopify-verification", "timestamp": "2026-06-11"}, separators=(',', ':')).encode('utf-8')

# Compute correct HMAC SHA-256 signature
signature = base64.b64encode(
    hmac.new(secret.encode('utf-8'), body, hashlib.sha256).digest()
).decode('utf-8')

print(f"Body: {body}")
print(f"Correct signature: {signature}")

# Request 1: Correctly signed
print("\n--- Sending correctly signed request ---")
req1 = urllib.request.Request(source_url, data=body, method='POST')
req1.add_header('Content-Type', 'application/json')
req1.add_header('X-Shopify-Hmac-Sha256', signature)
try:
    resp1 = urllib.request.urlopen(req1)
    print(f"Response 1 status: {resp1.status}")
    print(f"Response 1 body: {resp1.read().decode()}")
except Exception as e:
    print(f"Response 1 error: {e}")

# Request 2: Tampered (wrong signature)
print("\n--- Sending tampered request ---")
req2 = urllib.request.Request(source_url, data=body, method='POST')
req2.add_header('Content-Type', 'application/json')
req2.add_header('X-Shopify-Hmac-Sha256', 'wrong_signature_value')
try:
    resp2 = urllib.request.urlopen(req2)
    print(f"Response 2 status: {resp2.status}")
    print(f"Response 2 body: {resp2.read().decode()}")
except Exception as e:
    print(f"Response 2 error: {e}")

print("\nDone sending requests.")
