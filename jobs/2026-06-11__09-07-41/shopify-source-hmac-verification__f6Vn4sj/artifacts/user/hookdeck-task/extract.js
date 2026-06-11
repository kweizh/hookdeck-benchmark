const fs = require('fs');
const html = fs.readFileSync('/home/user/hookdeck-task/api-docs.html', 'utf8');

const regex = /props="({&quot;spec&quot;:.*?)">/;
const match = html.match(regex);
if (match) {
  const propsStr = match[1].replace(/&quot;/g, '"');
  fs.writeFileSync('/home/user/hookdeck-task/props.json', propsStr);
  console.log("Wrote props.json");
} else {
  console.log("Not found");
}
