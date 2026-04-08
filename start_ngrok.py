#!/usr/bin/env python3
"""Script para iniciar o servidor com ngrok - acesso público"""

import time
from pyngrok import ngrok

# Conectar ao servidor local
print("🌐 Iniciando ngrok...")
public_url = ngrok.connect(5000)

print("\n" + "="*60)
print("✅ SERVIDOR ONLINE - ACESSO PÚBLICO ATIVADO!")
print("="*60)
print(f"\n🔗 Link público: {public_url}")
print(f"\n📱 Compartilhe este link com qualquer pessoa:")
print(f"   {public_url}\n")
print("="*60)

# Manter rodando
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n👋 Encerrando...")
