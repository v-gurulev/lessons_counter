import requests, base64, os

r = requests.post('http://127.0.0.1:10086/command', json={
    'action': 'screenshot',
    'args': {'format': 'png'},
    'session': 'supabase-reset'
})

result = r.json()
if result.get('ok') and 'data' in result:
    data = result['data']
    img_data = data.get('data', '')
    path = 'supabase_sql.png'
    with open(path, 'wb') as f:
        f.write(base64.b64decode(img_data))
    print('Screenshot saved to', os.path.abspath(path))
else:
    print('Error:', result)
