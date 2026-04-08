import requests, json
fotos = requests.get('http://localhost:5000/uploads').json()
print('Deletando:', fotos[0]['id'])
r = requests.delete(f'http://localhost:5000/uploads/{fotos[0]["id"]}')
print('Status:', r.status_code)
print('Resposta:', r.json())
