const fs = require('fs');
const html = fs.readFileSync('/home/user/hookdeck-task/api-docs.html', 'utf8');

const regex = /"verification"/g;
let match;
while ((match = regex.exec(html)) !== null) {
  console.log(html.substring(match.index - 50, match.index + 200));
}
