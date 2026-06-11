const fs = require('fs');
const html = fs.readFileSync('/home/user/hookdeck-task/api-docs.html', 'utf8');

const index = html.indexOf('id="createsource"');
if (index !== -1) {
  console.log(html.substring(index, index + 3000));
} else {
  console.log("Not found");
}
