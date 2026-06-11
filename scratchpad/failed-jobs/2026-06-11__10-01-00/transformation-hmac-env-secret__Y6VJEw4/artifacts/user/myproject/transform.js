// Pure JavaScript HMAC-SHA256 implementation for Hookdeck Transformation
// No crypto module, no async/await, no fetch — V8 isolate compatible

// SHA-256 implementation
var sha256 = (function() {
  // SHA-256 constants
  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
  function ch(x, y, z) { return (x & y) ^ (~x & z); }
  function maj(x, y, z) { return (x & y) ^ (x & z) ^ (y & z); }
  function sigma0(x) { return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22); }
  function sigma1(x) { return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25); }
  function gamma0(x) { return rotr(x, 7) ^ rotr(x, 18) ^ (x >>> 3); }
  function gamma1(x) { return rotr(x, 17) ^ rotr(x, 19) ^ (x >>> 10); }

  function stringToUtf8Bytes(str) {
    var bytes = [];
    for (var i = 0; i < str.length; i++) {
      var c = str.charCodeAt(i);
      if (c < 0x80) {
        bytes.push(c);
      } else if (c < 0x800) {
        bytes.push(0xc0 | (c >>> 6), 0x80 | (c & 0x3f));
      } else if (c < 0xd800 || c >= 0xe000) {
        bytes.push(0xe0 | (c >>> 12), 0x80 | ((c >>> 6) & 0x3f), 0x80 | (c & 0x3f));
      } else {
        // surrogate pair
        i++;
        var cp = 0x10000 + ((c & 0x3ff) << 10) | (str.charCodeAt(i) & 0x3ff);
        bytes.push(0xf0 | (cp >>> 18), 0x80 | ((cp >>> 12) & 0x3f), 0x80 | ((cp >>> 6) & 0x3f), 0x80 | (cp & 0x3f));
      }
    }
    return bytes;
  }

  function wordsToHex(words) {
    var hex = '';
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      hex += ((w >>> 24) & 0xff).toString(16).padStart(2, '0');
      hex += ((w >>> 16) & 0xff).toString(16).padStart(2, '0');
      hex += ((w >>> 8) & 0xff).toString(16).padStart(2, '0');
      hex += (w & 0xff).toString(16).padStart(2, '0');
    }
    return hex;
  }

  function sha256(message) {
    var msgBytes;
    if (typeof message === 'string') {
      msgBytes = stringToUtf8Bytes(message);
    } else {
      msgBytes = message;
    }

    var msgLen = msgBytes.length;
    var bitLen = msgLen * 8;

    // Padding
    var padding = [0x80];
    var padLen = (56 - (msgLen + 1) % 64 + 64) % 64;
    for (var i = 0; i < padLen; i++) { padding.push(0); }

    // Append length as 64-bit big-endian
    // For messages < 2^53 bits, high 4 bytes are 0
    padding.push(0, 0, 0, 0);
    padding.push((msgLen >>> 24) & 0xff);
    padding.push((msgLen >>> 16) & 0xff);
    padding.push((msgLen >>> 8) & 0xff);
    padding.push(msgLen & 0xff);

    var allBytes = msgBytes.concat(padding);
    var blocks = [];
    for (var i = 0; i < allBytes.length; i += 64) {
      blocks.push(allBytes.slice(i, i + 64));
    }

    // Initial hash values
    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];

    for (var b = 0; b < blocks.length; b++) {
      var block = blocks[b];
      var W = new Array(64);

      for (var t = 0; t < 16; t++) {
        W[t] = (block[t * 4] << 24) | (block[t * 4 + 1] << 16) | (block[t * 4 + 2] << 8) | block[t * 4 + 3];
      }
      for (var t = 16; t < 64; t++) {
        W[t] = (gamma1(W[t - 2]) + W[t - 7] + gamma0(W[t - 15]) + W[t - 16]) >>> 0;
      }

      var a = H[0], b2 = H[1], c = H[2], d = H[3];
      var e = H[4], f = H[5], g = H[6], h = H[7];

      for (var t = 0; t < 64; t++) {
        var T1 = (h + sigma1(e) + ch(e, f, g) + K[t] + W[t]) >>> 0;
        var T2 = (sigma0(a) + maj(a, b2, c)) >>> 0;
        h = g; g = f; f = e; e = (d + T1) >>> 0;
        d = c; c = b2; b2 = a; a = (T1 + T2) >>> 0;
      }

      H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b2) >>> 0;
      H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0;
      H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }

    return wordsToHex(H);
  }

  return sha256;
})();

// HMAC-SHA256
function hmacSha256(key, message) {
  var blockSize = 64; // 64 bytes for SHA-256

  // Convert key to bytes
  var keyBytes;
  if (typeof key === 'string') {
    keyBytes = [];
    for (var i = 0; i < key.length; i++) {
      var c = key.charCodeAt(i);
      if (c < 0x80) {
        keyBytes.push(c);
      } else if (c < 0x800) {
        keyBytes.push(0xc0 | (c >>> 6), 0x80 | (c & 0x3f));
      } else {
        keyBytes.push(0xe0 | (c >>> 12), 0x80 | ((c >>> 6) & 0x3f), 0x80 | (c & 0x3f));
      }
    }
  } else {
    keyBytes = key;
  }

  // If key is longer than block size, hash it
  if (keyBytes.length > blockSize) {
    var hashHex = sha256(keyBytes);
    keyBytes = [];
    for (var i = 0; i < hashHex.length; i += 2) {
      keyBytes.push(parseInt(hashHex.substr(i, 2), 16));
    }
  }

  // Pad key to block size
  var oKeyPad = [];
  var iKeyPad = [];
  for (var i = 0; i < blockSize; i++) {
    var byteVal = i < keyBytes.length ? keyBytes[i] : 0;
    oKeyPad.push(byteVal ^ 0x5c);
    iKeyPad.push(byteVal ^ 0x36);
  }

  // Convert message to bytes
  var msgBytes;
  if (typeof message === 'string') {
    msgBytes = [];
    for (var i = 0; i < message.length; i++) {
      var c = message.charCodeAt(i);
      if (c < 0x80) {
        msgBytes.push(c);
      } else if (c < 0x800) {
        msgBytes.push(0xc0 | (c >>> 6), 0x80 | (c & 0x3f));
      } else {
        msgBytes.push(0xe0 | (c >>> 12), 0x80 | ((c >>> 6) & 0x3f), 0x80 | (c & 0x3f));
      }
    }
  } else {
    msgBytes = message;
  }

  var innerHash = sha256(iKeyPad.concat(msgBytes));
  // Convert hex innerHash back to bytes
  var innerBytes = [];
  for (var i = 0; i < innerHash.length; i += 2) {
    innerBytes.push(parseInt(innerHash.substr(i, 2), 16));
  }

  return sha256(oKeyPad.concat(innerBytes));
}

// Hookdeck Transformation Handler
addHandler("transform", function(request, context) {
  var secret = process.env.MY_SECRET;
  var bodyString = JSON.stringify(request.body);
  var signature = hmacSha256(secret, bodyString);
  var signedAt = new Date().toISOString();

  request.headers["x-hd-signature"] = signature;
  request.headers["x-hd-signed-at"] = signedAt;

  return request;
});
