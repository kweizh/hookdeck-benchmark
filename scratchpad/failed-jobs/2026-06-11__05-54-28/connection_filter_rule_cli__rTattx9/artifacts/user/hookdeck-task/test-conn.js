async function run() {
  const res = await fetch("https://api.hookdeck.com/2024-09-01/connections", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + process.env.HOOKDECK_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: "filtered-conn-" + process.env.ZEALT_RUN_ID,
      source: {
        name: "my-source-" + process.env.ZEALT_RUN_ID
      },
      destination: {
        name: "my-dest-" + process.env.ZEALT_RUN_ID,
        url: "https://mock.hookdeck.com"
      },
      rules: [
        {
          type: "filter",
          body: {
            amount: {
              $gt: 100
            }
          }
        }
      ]
    })
  });
  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}
run();
