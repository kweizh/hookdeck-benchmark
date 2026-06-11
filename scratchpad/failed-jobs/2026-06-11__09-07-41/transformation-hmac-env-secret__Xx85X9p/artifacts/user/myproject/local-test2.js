const crypto = require('crypto');
const secret = "s3cr3t-zr-xx85x9p";
const message = JSON.stringify({ hello: "world" });
const hmac = crypto.createHmac('sha256', secret);
hmac.update(message);
console.log(hmac.digest('hex'));
