const fs = require('fs');
const props = JSON.parse(fs.readFileSync('/home/user/hookdeck-task/props.json', 'utf8'));

// The spec is in props.spec. It's a devalue array.
// Actually, let's just write a script to look at the schema for CreateSource.
const str = fs.readFileSync('/home/user/hookdeck-task/props.json', 'utf8');

// Let's just regex for SourceVerification or similar in the string.
const verificationIndex = str.indexOf('SourceVerification');
if (verificationIndex !== -1) {
  console.log(str.substring(verificationIndex - 100, verificationIndex + 500));
}

const shopifyIndex = str.indexOf('shopify');
console.log("shopify at", shopifyIndex);
