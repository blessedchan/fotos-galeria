# 📸 Galeria de Fotos com Upload

Sistema de galeria VSCO-estilo com upload de fotos, armazenamento persistente e acesso em rede.

## 🚀 Recursos

✅ Galeria responsiva (mobile, tablet, desktop)  
✅ Upload de fotos com Flask backend  
✅ Armazenamento persistente (JSON + disco)  
✅ Delete e download de fotos  
✅ Compartilhamento em rede local  
✅ Acesso remoto com ngrok ou deploy em cloud  

## 📋 Tecnologias

- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Backend**: Python Flask + Werkzeug
- **Banco de Dados**: JSON file-based
- **Estilos**: VSCO aesthetic (cream, brown, tan colors)

## 🛠️ Como usar localmente

### Requisitos
- Python 3.10+
- pip

### Instalação

```bash
# Clonar repositório
git clone https://github.com/SEU_USUARIO/galeria-fotos.git
cd galeria-fotos

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### Rodar localmente

```bash
python index.py
```

Depois acesse: http://localhost:5000

### Compartilhar na rede local

O servidor já roda em `0.0.0.0:5000`, então outras pessoas podem acessar:
```
http://SEU_IP:5000
```

## ☁️ Deploy no Railway (Recomendado)

1. Vá para https://railway.app
2. Clique "New project" → "Deploy from GitHub"
3. Conecte seu GitHub e selecione o repositório
4. Railway detecta automaticamente Python
5. Deploy em poucos minutos!

URL do seu app: `https://seu-app.railway.app`

## 📁 Estrutura

```
.
├── index.py              # Servidor Flask
├── album.html            # Galeria principal
├── upload.html           # Página de upload
├── requirements.txt      # Dependências Python
├── Procfile             # Config para Railway
├── uploads/             # Pasta com fotos (criada automaticamente)
├── uploads_metadata.json # Metadados das fotos
└── .gitignore           # Arquivos ignorados
```

## 🔧 API Endpoints

- `GET /` - Página principal (album.html)
- `POST /upload` - Upload de foto
- `GET /uploads` - Lista todas as fotos (JSON)
- `DELETE /uploads/<id>` - Deletar foto
- `GET /uploads/<filename>` - Baixar foto

## 📝 Variáveis de Ambiente

```bash
PORT=5000          # Porta do servidor
DEBUG=True         # Modo debug (desabilitar em produção)
```

## 🤝 Contribuições

Sinta-se livre para fazer fork, melhorias e PRs!

## 📄 Licença

MIT License

---

**Feito com ❤️**
