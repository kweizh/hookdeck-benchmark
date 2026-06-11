#!/bin/bash

if [ -z "$ZEALT_RUN_ID" ]; then
  echo "ZEALT_RUN_ID is not set"
  exit 1
fi

RUN_ID="$ZEALT_RUN_ID"

echo "Authenticating..."
hookdeck ci

echo "Creating Source source-${RUN_ID}..."
hookdeck gateway source create --name "source-${RUN_ID}" --type WEBHOOK --output json > source.json
SOURCE_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" < source.json)

echo "Creating Destination dest-${RUN_ID}..."
hookdeck gateway destination create --name "dest-${RUN_ID}" --type MOCK_API --output json > dest.json
DEST_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" < dest.json)

echo "Creating Transformation flatten-${RUN_ID}..."
cat << 'EOF' > transform.js
addHandler("transform", (request, context) => {
  if (request.body && request.body.data && request.body.data.object) {
    request.body = request.body.data.object;
  }
  return request;
});
EOF

hookdeck gateway transformation create --name "flatten-${RUN_ID}" --code-file transform.js --output json > transform.json
TRANSFORM_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" < transform.json)

echo "Creating Connection conn-${RUN_ID}..."
hookdeck gateway connection create \
  --name "conn-${RUN_ID}" \
  --source-id "$SOURCE_ID" \
  --destination-id "$DEST_ID" \
  --rule-transform-name "$TRANSFORM_ID" \
  --output json > connection.json

echo "Setup complete"
