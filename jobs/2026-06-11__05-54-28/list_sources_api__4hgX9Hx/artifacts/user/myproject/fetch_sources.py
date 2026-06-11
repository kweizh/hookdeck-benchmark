import os
import requests

api_key = os.environ.get('HOOKDECK_API_KEY')
headers = {'Authorization': f'Bearer {api_key}'}
url = 'https://api.hookdeck.com/2024-03-01/sources'
names = []

while url:
    response = requests.get(url, headers=headers)
    data = response.json()
    for model in data.get('models', []):
        names.append(model['name'])
    
    next_cursor = data.get('pagination', {}).get('next')
    if next_cursor:
        url = f'https://api.hookdeck.com/2024-03-01/sources?next={next_cursor}'
    else:
        url = None

with open('/home/user/myproject/sources.txt', 'w') as f:
    for name in names:
        f.write(name + '\n')
