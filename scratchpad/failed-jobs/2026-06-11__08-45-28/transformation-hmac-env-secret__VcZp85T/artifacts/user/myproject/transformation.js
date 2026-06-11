// Pure-JS SHA-256 and HMAC-SHA256 (no Node built-ins, V8 isolate safe)
function sha256(message) {
  var K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];
  var H = [
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
  ];

  // Convert string to bytes (UTF-8)
  var bytes = [];
  for (var i = 0; i < message.length; i++) {
    var c = message.charCodeAt(i);
    if (c < 128) {
      bytes.push(c);
    } else if (c < 2048) {
      bytes.push((c >> 6) | 192);
      bytes.push((c & 63) | 128);
    } else if (c < 55296 || c >= 57344) {
      bytes.push((c >> 12) | 224);
      bytes.push(((c >> 6) & 63) | 128);
      bytes.push((c & 63) | 128);
    } else {
      i++;
      c = 0x10000 + (((c & 1023) << 10) | (message.charCodeAt(i) & 1023));
      bytes.push((c >> 18) | 240);
      bytes.push(((c >> 12) & 63) | 128);
      bytes.push(((c >> 6) & 63) | 128);
      bytes.push((c & 63) | 128);
    }
  }

  var bitLen = bytes.length * 8;
  bytes.push(0x80);
  while ((bytes.length % 64) !== 56) bytes.push(0);
  // Append 64-bit big-endian bit length (only lower 32 bits since JS numbers)
  bytes.push(0); bytes.push(0); bytes.push(0); bytes.push(0);
  bytes.push((bitLen >>> 24) & 0xff);
  bytes.push((bitLen >>> 16) & 0xff);
  bytes.push((bitLen >>> 8) & 0xff);
  bytes.push(bitLen & 0xff);

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
  function safe_add(x, y) {
    var lsw = (x & 0xffff) + (y & 0xffff);
    var msw = (x >> 16) + (y >> 16) + (lsw >> 16);
    return (msw << 16) | (lsw & 0xffff);
  }

  for (var chunk = 0; chunk < bytes.length; chunk += 64) {
    var w = [];
    for (var j = 0; j < 16; j++) {
      w[j] = (bytes[chunk + j*4] << 24) | (bytes[chunk + j*4+1] << 16) |
              (bytes[chunk + j*4+2] << 8) | bytes[chunk + j*4+3];
    }
    for (var j = 16; j < 64; j++) {
      var s0 = rotr(w[j-15], 7) ^ rotr(w[j-15], 18) ^ (w[j-15] >>> 3);
      var s1 = rotr(w[j-2], 17) ^ rotr(w[j-2], 19) ^ (w[j-2] >>> 10);
      w[j] = safe_add(safe_add(w[j-16], s0), safe_add(w[j-7], s1));
    }
    var a=H[0], b=H[1], c=H[2], d=H[3], e=H[4], f=H[5], g=H[6], h=H[7];
    for (var j = 0; j < 64; j++) {
      var S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
      var ch = (e & f) ^ (~e & g);
      var temp1 = safe_add(safe_add(h, S1), safe_add(ch, safe_add(K[j], w[j])));
      var S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
      var maj = (a & b) ^ (a & c) ^ (b & c);
      var temp2 = safe_add(S0, maj);
      h=g; g=f; f=e; e=safe_add(d,temp1);
      d=c; c=b; b=a; a=safe_add(temp1,temp2);
    }
    H[0]=safe_add(H[0],a); H[1]=safe_add(H[1],b); H[2]=safe_add(H[2],c); H[3]=safe_add(H[3],d);
    H[4]=safe_add(H[4],e); H[5]=safe_add(H[5],f); H[6]=safe_add(H[6],g); H[7]=safe_add(H[7],h);
  }

  var hashBytes = [];
  for (var i = 0; i < 8; i++) {
    hashBytes.push((H[i] >>> 24) & 0xff);
    hashBytes.push((H[i] >>> 16) & 0xff);
    hashBytes.push((H[i] >>> 8) & 0xff);
    hashBytes.push(H[i] & 0xff);
  }
  return hashBytes;
}

function hmacSha256(key, message) {
  var blockSize = 64;

  // Convert key to bytes
  function strToBytes(s) {
    var b = [];
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c < 128) {
        b.push(c);
      } else if (c < 2048) {
        b.push((c >> 6) | 192);
        b.push((c & 63) | 128);
      } else {
        b.push((c >> 12) | 224);
        b.push(((c >> 6) & 63) | 128);
        b.push((c & 63) | 128);
      }
    }
    return b;
  }

  function bytesToStr(bytes) {
    var s = '';
    for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return s;
  }

  var keyBytes = strToBytes(key);
  if (keyBytes.length > blockSize) keyBytes = sha256(bytesToStr(keyBytes));
  while (keyBytes.length < blockSize) keyBytes.push(0);

  var opad = [], ipad = [];
  for (var i = 0; i < blockSize; i++) {
    opad.push(keyBytes[i] ^ 0x5c);
    ipad.push(keyBytes[i] ^ 0x36);
  }

  var ipadStr = bytesToStr(ipad) + message;
  var innerHash = sha256(ipadStr);
  var outerInput = bytesToStr(opad) + bytesToStr(innerHash);
  var result = sha256(outerInput);

  var hex = '';
  for (var i = 0; i < result.length; i++) {
    hex += ('0' + result[i].toString(16)).slice(-2);
  }
  return hex;
}

// Main transformation handler
function handler(request, context) {
  var secret = process.env.MY_SECRET;
  var body = JSON.stringify(request.body);
  var signature = hmacSha256(secret, body);
  var signedAt = new Date().toISOString();

  request.headers['x-hd-signature'] = signature;
  request.headers['x-hd-signed-at'] = signedAt;

  return request;
}
