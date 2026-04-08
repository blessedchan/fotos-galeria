#!/usr/bin/env python3
"""Script para configurar ngrok automaticamente"""

import subprocess
import sys

print("="*60)
print("🔐 CONFIGURAR NGROK PARA ACESSO PÚBLICO")
print("="*60)

print("\n1️⃣  Vá para: https://ngrok.com")
print("2️⃣  Clique em 'Sign Up' (cadastro gratuito)")
print("3️⃣  Verifique seu email")
print("4️⃣  No dashboard, copie o 'authtoken' (começa com 4_...)")
print("\n" + "-"*60)

authtoken = input("\n🔑 Cole seu authtoken aqui: ").strip()

if not authtoken:
    print("❌ Nenhum token fornecido!")
    sys.exit(1)

print(f"\n⏳ Configurando ngrok...")
try:
    # Configurar ngrok
    subprocess.run(["ngrok", "authtoken", authtoken], check=True)
    print("✅ ngrok configurado com sucesso!")
    
    # Testar ngrok
    print("\n✅ Iniciando ngrok...")
    print("🔗 Link público será gerado em 3 segundos...\n")
    
    # Usar pyngrok para gerar o link
    from pyngrok import ngrok
    import time
    
    url = ngrok.connect(5000)
    print("="*60)
    print("✅ SERVIDOR ONLINE COM ACESSO PÚBLICO!")
    print("="*60)
    print(f"\n🌐 Link público: {url}")
    print(f"\n📱 Compartilhe com pessoas de fora:")
    print(f"   {url}\n")
    print("⚠️  Este script precisa ficar rodando!")
    print("   (Feche com Ctrl+C quando quiser parar)\n")
    print("="*60)
    
    # Manter rodando
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n👋 Encerrando...")
except Exception as e:
    print(f"❌ Erro: {e}")
    print("\n💡 Dica: Certifique-se que tem ngrok instalado:")
    print("   pip install pyngrok")
