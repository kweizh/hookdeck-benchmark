const https = require('https');

https.get('https://hookdeck.com/docs/api', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // Just save it to a file
    require('fs').writeFileSync('/home/user/hookdeck-task/api-docs.html', data);
  });
});
