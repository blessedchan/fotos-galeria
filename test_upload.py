#!/usr/bin/env python3
"""Script de teste para debug do upload"""

import requests
import json
from pathlib import Path

# URL do servidor
BASE_URL = "http://localhost:5000"

# Criar uma imagem PIN PNG mínima para teste
png_bytes = bytes([
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,  # PNG signature
    0x00, 0x00, 0x00, 0x0d,  # IHDR chunk size
    0x49, 0x48, 0x44, 0x52,  # IHDR
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 image
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90,              # 8-bit RGB
    0x77, 0x53, 0xde,                                 # CRC
    0x00, 0x00, 0x00, 0x0c,                          # IDAT chunk size
    0x49, 0x44, 0x41, 0x54,                          # IDAT
    0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0xfe, 0xff, # Compressed data
    0x00, 0x00, 0x00, 0x02,                          # More data
    0x00, 0x02, 0xfe, 0xdc, 0xcc,                    # CRC
    0x00, 0x00, 0x00, 0x00,                          # IEND chunk size
    0x49, 0x45, 0x4e, 0x44,                          # IEND
    0xae, 0x42, 0x60, 0x82                           # CRC
])

test_file = Path("test_image_1x1.png")
test_file.write_bytes(png_bytes)

print(f"✓ Arquivo de teste criado: {test_file} ({len(png_bytes)} bytes)")

# Teste 1: GET /uploads (lista vazia)
print("\n[TESTE 1] GET /uploads")
try:
    r = requests.get(f"{BASE_URL}/uploads")
    print(f"  Status: {r.status_code}")
    print(f"  Tipo: {r.headers.get('content-type')}")
    print(f"  Conteúdo: {r.text}")
    print(f"  JSON parseado: {r.json()}")
except Exception as e:
    print(f"  ERRO: {e}")

# Teste 2: POST /upload com arquivo válido
print("\n[TESTE 2] POST /upload (com arquivo válido)")
try:
    with open(test_file, 'rb') as f:
        files = {'arquivo': f}
        data = {
            'usuario': 'Test User',
            'data': '2026-04-07'
        }
        r = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    
    print(f"  Status: {r.status_code}")
    print(f"  Tipo: {r.headers.get('content-type')}")
    print(f"  Tamanho resposta: {len(r.text)} bytes")
    print(f"  Conteúdo: {r.text}")
    
    if r.text:
        try:
            result = r.json()
            print(f"  JSON parseado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print(f"  ERRO ao fazer parse do JSON")
except Exception as e:
    print(f"  ERRO: {e}")

# Teste 3: Verificar uploads agora
print("\n[TESTE 3] GET /uploads (após upload)")
try:
    r = requests.get(f"{BASE_URL}/uploads")
    print(f"  Status: {r.status_code}")
    print(f"  Conteúdo: {r.text}")
    if r.text:
        result = r.json()
        print(f"  Total de fotos: {len(result)}")
        if result:
            print(f"  Primeira foto: {json.dumps(result[0], indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n✅ Testes concluídos!")
