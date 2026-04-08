from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
METADATA_FILE = BASE_DIR / "uploads_metadata.json"
COMMENTS_FILE = BASE_DIR / "comments.json"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=".")
CORS(app)  # Habilitar CORS para todas as rotas


def _load_metadata() -> list[dict]:
    if not METADATA_FILE.exists():
        return []
    with METADATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_metadata(entries: list[dict]) -> None:
    with METADATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _load_comments() -> dict:
    """Carregar comentários de todas as fotos"""
    if not COMMENTS_FILE.exists():
        return {}
    with COMMENTS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_comments(comments: dict) -> None:
    """Salvar comentários em JSON"""
    with COMMENTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


def _is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "album.html")


@app.get("/album.html")
def album():
    return send_from_directory(BASE_DIR, "album.html")


@app.get("/upload.html")
def upload_page():
    return send_from_directory(BASE_DIR, "upload.html")


@app.post("/upload")
def upload():
    username = (request.form.get("usuario") or "").strip()
    custom_date = (request.form.get("data") or "").strip()
    uploaded_file = request.files.get("arquivo")

    if not username:
        return jsonify({"ok": False, "error": "Campo 'usuario' é obrigatório."}), 400
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo para upload."}), 400
    if not _is_allowed(uploaded_file.filename):
        return jsonify({"ok": False, "error": "Tipo de arquivo não permitido."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    unique_name = f"{uuid4().hex}_{safe_name}"
    destination = UPLOAD_DIR / unique_name
    uploaded_file.save(destination)

    now_iso = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": uuid4().hex,
        "arquivo_original": uploaded_file.filename,
        "arquivo_salvo": unique_name,
        "usuario": username,
        "data_evento": custom_date if custom_date else None,
        "data_upload_utc": now_iso,
        "url_arquivo": f"/uploads/{unique_name}",
    }

    entries = _load_metadata()
    entries.append(entry)
    _save_metadata(entries)

    return jsonify({"ok": True, "item": entry}), 201


@app.get("/uploads")
def list_uploads():
    entries = _load_metadata()
    return jsonify(entries)


@app.get("/uploads/<path:filename>")
def serve_upload(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.delete("/uploads/<photo_id>")
def delete_photo(photo_id: str):
    """Deletar uma foto pelo ID"""
    entries = _load_metadata()
    photo_to_delete = None
    
    for entry in entries:
        if entry["id"] == photo_id:
            photo_to_delete = entry
            break
    
    if not photo_to_delete:
        return jsonify({"ok": False, "error": "Foto não encontrada"}), 404
    
    # Remover arquivo do disco
    file_path = UPLOAD_DIR / photo_to_delete["arquivo_salvo"]
    if file_path.exists():
        file_path.unlink()
    
    # Remover do metadata
    entries = [e for e in entries if e["id"] != photo_id]
    _save_metadata(entries)
    
    return jsonify({"ok": True, "message": "Foto deletada com sucesso"}), 200


@app.get("/comments/<photo_id>")
def get_comments(photo_id: str):
    """Carregar comentários de uma foto"""
    comments = _load_comments()
    photo_comments = comments.get(photo_id, [])
    return jsonify(photo_comments), 200


@app.post("/comments")
def add_comment():
    """Adicionar comentário a uma foto"""
    data = request.get_json()
    
    photo_id = (data.get("photo_id") or "").strip()
    usuario = (data.get("usuario") or "").strip()
    texto = (data.get("texto") or "").strip()
    
    if not photo_id or not usuario or not texto:
        return jsonify({"ok": False, "error": "Campos obrigatórios faltando"}), 400
    
    comment = {
        "id": uuid4().hex,
        "usuario": usuario,
        "texto": texto,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    comments = _load_comments()
    if photo_id not in comments:
        comments[photo_id] = []
    
    comments[photo_id].append(comment)
    _save_comments(comments)
    
    return jsonify({"ok": True, "comment": comment}), 201


@app.delete("/comments/<comment_id>")
def delete_comment(comment_id: str):
    """Deletar um comentário"""
    comments = _load_comments()
    
    for photo_id in comments:
        comments[photo_id] = [c for c in comments[photo_id] if c["id"] != comment_id]
    
    _save_comments(comments)
    return jsonify({"ok": True, "message": "Comentário deletado"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
