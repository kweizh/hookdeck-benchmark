const fs = require('fs');
const html = fs.readFileSync('/home/user/hookdeck-task/api-docs.html', 'utf8');

const index = html.indexOf('Create a source');
if (index !== -1) {
  console.log(html.substring(index - 200, index + 2000));
} else {
  console.log("Not found");
}
