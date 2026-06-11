const request = {
  body: { hello: "world" },
  headers: {}
};
process.env.MY_SECRET = "s3cr3t-zr-xx85x9p";

// Pure JS HMAC-SHA256
function transform(request) {
  // SHA256 implementation
  function sha256(ascii) {
      function rightRotate(value, amount) {
          return (value >>> amount) | (value << (32 - amount));
      }
      
      var mathPow = Math.pow;
      var maxWord = mathPow(2, 32);
      var lengthProperty = 'length';
      var i, j; // Used as a counter across the whole file
      var result = '';

      var words = [];
      var asciiBitLength = ascii[lengthProperty] * 8;
      
      var hash = sha256.h = sha256.h || [];
      var k = sha256.k = sha256.k || [];
      var primeCounter = k[lengthProperty];

      var isComposite = {};
      for (var candidate = 2; primeCounter < 64; candidate++) {
          if (!isComposite[candidate]) {
              for (i = 0; i < 313; i += candidate) {
                  isComposite[i] = candidate;
              }
              hash[primeCounter] = (mathPow(candidate, .5) * maxWord) | 0;
              k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
          }
      }
      
      ascii += '\x80'; // Append Ƈ' bit (plus zero padding)
      while (ascii[lengthProperty] % 64 - 56) ascii += '\x00'; // More zero padding
      for (i = 0; i < ascii[lengthProperty]; i++) {
          j = ascii.charCodeAt(i);
          if (j >> 8) return; // ASCII check: only accept characters in range 0-255
          words[i >> 2] |= j << ((3 - i % 4) * 8);
      }
      words[words[lengthProperty]] = ((asciiBitLength / maxWord) | 0);
      words[words[lengthProperty]] = (asciiBitLength)

      // process each chunk
      for (j = 0; j < words[lengthProperty];) {
          var w = words.slice(j, j += 16); // The message is expanded into 64 words as part of the iteration
          var oldHash = hash;
          hash = hash.slice(0, 8);
          
          for (i = 0; i < 64; i++) {
              var i2 = i + j;
              var w15 = w[i - 15], w2 = w[i - 2];
              var a = hash[0], e = hash[4];
              var temp1 = hash[7]
                  + (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25)) // S1
                  + ((e&hash[5])^((~e)&hash[6])) // ch
                  + k[i]
                  + (w[i] = (i < 16) ? w[i] : (
                          w[i - 16]
                          + (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3)) // s0
                          + w[i - 7]
                          + (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10)) // s1
                      )|0
                  );
              var temp2 = (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22)) // S0
                  + ((a&hash[1])^(a&hash[2])^(hash[1]&hash[2])); // maj
              
              hash = [(temp1 + temp2)|0].concat(hash);
              hash[4] = (hash[4] + temp1)|0;
          }
          
          for (i = 0; i < 8; i++) {
              hash[i] = (hash[i] + oldHash[i])|0;
          }
      }
      
      for (i = 0; i < 8; i++) {
          for (j = 3; j + 1; j--) {
              var b = (hash[i] >> (j * 8)) & 255;
              result += ((b < 16) ? 0 : '') + b.toString(16);
          }
      }
      return result;
  }

  function hexToBytes(hex) {
      var bytes = [];
      for (var c = 0; c < hex.length; c += 2) {
          bytes.push(parseInt(hex.substr(c, 2), 16));
      }
      return bytes;
  }

  function bytesToStr(bytes) {
      var str = '';
      for (var i = 0; i < bytes.length; i++) {
          str += String.fromCharCode(bytes[i]);
      }
      return str;
  }

  function hmac_sha256(key, message) {
      var blockSize = 64;
      
      var keyStr = key;
      if (keyStr.length > blockSize) {
          keyStr = bytesToStr(hexToBytes(sha256(keyStr)));
      }
      if (keyStr.length < blockSize) {
          while (keyStr.length < blockSize) keyStr += '\x00';
      }
      
      var o_key_pad = '';
      var i_key_pad = '';
      for (var i = 0; i < blockSize; i++) {
          o_key_pad += String.fromCharCode(keyStr.charCodeAt(i) ^ 0x5c);
          i_key_pad += String.fromCharCode(keyStr.charCodeAt(i) ^ 0x36);
      }
      
      return sha256(o_key_pad + bytesToStr(hexToBytes(sha256(i_key_pad + message))));
  }

  const secret = process.env.MY_SECRET;
  const message = JSON.stringify(request.body);
  const signature = hmac_sha256(secret, message).toLowerCase();
  
  request.headers = request.headers || {};
  request.headers['x-hd-signature'] = signature;
  request.headers['x-hd-signed-at'] = new Date().toISOString();
  
  return request;
}

console.log(transform(request));
