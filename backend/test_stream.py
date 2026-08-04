import requests, json
r = requests.post('http://127.0.0.1:8000/api/agent/stream',
                  json={'message': 'say hi in 1 word', 'session_id': 'test_conn'},
                  stream=True, timeout=300)
print('Status:', r.status_code)
for line in r.iter_lines():
    if not line:
        continue
    decoded = line.decode()
    if not decoded.startswith('data: '):
        continue
    event = json.loads(decoded[6:])
    print(f"{event.get('stage')}: {str(event.get('message', ''))[:60]}")
    if event.get('stage') == 'done':
        print('Reply:', str(event.get('reply', ''))[:100])
        break
    if event.get('stage') == 'error':
        print('Error:', event.get('message'))
        break