const fs = require('fs');
const html = fs.readFileSync('/home/user/hookdeck-task/api-docs.html', 'utf8');

const regex = /<h2[^>]*id="createsource"[^>]*>.*?<\/h2>(.*?)<h2/s;
const match = html.match(regex);
if (match) {
  console.log(match[1].substring(0, 3000));
} else {
  console.log("Not found");
}
