#!/bin/bash
set -e

RUN_ID="zr-kisqemd"
API_KEY="REDACTED"
BASE_URL="https://api.hookdeck.com"

SRC_NAME="hmac-src-${RUN_ID}"
DST_NAME="hmac-dst-${RUN_ID}"
TRF_NAME="hmac-trf-${RUN_ID}"
CONN_NAME="hmac-conn-${RUN_ID}"
SECRET="s3cr3t-${RUN_ID}"

echo "=== Creating Source ==="
SRC_RESPONSE=$(curl -s -X POST "${BASE_URL}/sources" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${SRC_NAME}\",
    \"type\": \"WEBHOOK\"
  }")
echo "$SRC_RESPONSE"
SRC_ID=$(echo "$SRC_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Source ID: $SRC_ID"

echo "=== Creating Destination ==="
DST_RESPONSE=$(curl -s -X POST "${BASE_URL}/destinations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${DST_NAME}\",
    \"type\": \"MOCK_API\",
    \"url\": \"https://mock.hookdeck.com/hooks/${RUN_ID}\"
  }")
echo "$DST_RESPONSE"
DST_ID=$(echo "$DST_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Destination ID: $DST_ID"

echo "=== Creating Transformation ==="
# Pure JS HMAC-SHA256 implementation for V8 isolate
TRF_CODE=$(cat <<'TRANSEOF'
var sha256_k = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];

function toHex(n){var h='';for(var i=0;i<8;i++){h+=((n>>>(28-i*4))&0xf).toString(16);}return h;}

function sha256(msg){var M=msgToBlocks(msg);var H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];for(var i=0;i<M.length;i++){var W=M[i];for(var j=16;j<64;j++){var s0=ror(W[j-15],7)^ror(W[j-15],18)^(W[j-15]>>>3);var s1=ror(W[j-2],17)^ror(W[j-2],19)^(W[j-2]>>>10);W[j]=(W[j-16]+s0+W[j-7]+s1)|0;}var a=H[0],b=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];for(var j=0;j<64;j++){var S1=ror(e,6)^ror(e,11)^ror(e,25);var ch=(e&f)^(~e&g);var temp1=(h+S1+ch+sha256_k[j]+W[j])|0;var S0=ror(a,2)^ror(a,13)^ror(a,22);var maj=(a&b)^(a&c)^(b&c);var temp2=(S0+maj)|0;h=g;g=f;f=e;e=(d+temp1)|0;d=c;c=b;b=a;a=(temp1+temp2)|0;}H[0]=(H[0]+a)|0;H[1]=(H[1]+b)|0;H[2]=(H[2]+c)|0;H[3]=(H[3]+d)|0;H[4]=(H[4]+e)|0;H[5]=(H[5]+f)|0;H[6]=(H[6]+g)|0;H[7]=(H[7]+h)|0;}var digest='';for(var i=0;i<8;i++)digest+=toHex(H[i]);return digest;}

function ror(x,n){return((x>>>n)|(x<<(32-n)))&0xffffffff;}

function msgToBlocks(msg){var bytes=unescape(encodeURIComponent(msg));var len=bytes.length;var bitLen=len*8;var padLen=((56-((len+1)%64))+64)%64;var totalLen=len+1+padLen+8;var data=[];for(var i=0;i<totalLen;i++)data.push(0);for(var i=0;i<len;i++)data[i]=bytes.charCodeAt(i);data[len]=0x80;for(var i=0;i<4;i++)data[totalLen-1-i]=(bitLen>>>(i*8))&0xff;var blocks=[];for(var i=0;i<data.length;i+=64){var W=[];for(var j=0;j<16;j++){W[j]=(data[i+j*4]<<24)|(data[i+j*4+1]<<16)|(data[i+j*4+2]<<8)|data[i+j*4+3];W[j]=W[j]>>>0;}blocks.push(W);}return blocks;}

function hmacSha256(key,msg){if(key.length>64)key=sha256(key);while(key.length<64)key+='\x00';var oKeyPad='',iPad='';for(var i=0;i<64;i++){var kc=key.charCodeAt?key.charCodeAt(i):0;oKeyPad+=String.fromCharCode(kc^0x5c);iPad+=String.fromCharCode(kc^0x36);}return sha256(oKeyPad+sha256(iPad+msg));}

module.exports=function(request){var body=JSON.stringify(request.body);var sig=hmacSha256(process.env.MY_SECRET,body);var ts=new Date().toISOString();return{headers:Object.assign({},request.headers||{},{'x-hd-signature':sig,'x-hd-signed-at':ts}),body:request.body};};
TRANSEOF
)

# Escape the code for JSON
TRF_CODE_ESCAPED=$(echo "$TRF_CODE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")

TRF_RESPONSE=$(curl -s -X POST "${BASE_URL}/transformations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${TRF_NAME}\",
    \"code\": ${TRF_CODE_ESCAPED},
    \"env\": {
      \"MY_SECRET\": \"${SECRET}\"
    }
  }")
echo "$TRF_RESPONSE"
TRF_ID=$(echo "$TRF_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Transformation ID: $TRF_ID"

echo "=== Creating Connection ==="
CONN_RESPONSE=$(curl -s -X POST "${BASE_URL}/connections" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${CONN_NAME}\",
    \"source\": {
      \"id\": \"${SRC_ID}\"
    },
    \"destination\": {
      \"id\": \"${DST_ID}\"
    },
    \"rules\": [
      {
        \"type\": \"transform\",
        \"transformation_id\": \"${TRF_ID}\"
      }
    ]
  }")
echo "$CONN_RESPONSE"
CONN_ID=$(echo "$CONN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Connection ID: $CONN_ID"

echo "=== Writing output.log ==="
cat > /home/user/myproject/output.log <<LOGEOF
Source Name: ${SRC_NAME}
Destination Name: ${DST_NAME}
Connection ID: ${CONN_ID}
Transformation ID: ${TRF_ID}
LOGEOF

echo "=== Done ==="
cat /home/user/myproject/output.log