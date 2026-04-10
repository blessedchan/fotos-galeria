from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from uuid import uuid4

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
METADATA_FILE = BASE_DIR / "uploads_metadata.json"
COMMENTS_FILE = BASE_DIR / "comments.json"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
}
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024))
MAX_COMMENT_LENGTH = int(os.environ.get("MAX_COMMENT_LENGTH", 1000))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", 60))
RATE_LIMIT_WRITE_REQUESTS = int(os.environ.get("RATE_LIMIT_WRITE_REQUESTS", 30))
ADMIN_DELETE_TOKEN = os.environ.get("ADMIN_DELETE_TOKEN", "").strip()
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "").strip()
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip()
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
HEX_ID_RE = re.compile(r"^[0-9a-f]{32}$")
RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}
PUBLIC_ENDPOINTS = {"login_page", "login", "logout"}

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=".")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
app.config["SECRET_KEY"] = SECRET_KEY or os.urandom(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"

if FRONTEND_ORIGIN:
    CORS(app, resources={r"/*": {"origins": [FRONTEND_ORIGIN]}})


def _load_metadata() -> list[dict]:
    if not METADATA_FILE.exists():
        return []
    try:
        with METADATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save_metadata(entries: list[dict]) -> None:
    with METADATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _load_comments() -> dict:
    if not COMMENTS_FILE.exists():
        return {}
    try:
        with COMMENTS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_comments(comments: dict) -> None:
    with COMMENTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


def _is_allowed(filename: str, mimetype: str | None) -> bool:
    return (
        Path(filename).suffix.lower() in ALLOWED_EXTENSIONS
        and (mimetype or "").lower() in ALLOWED_MIME_TYPES
    )


def _client_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _enforce_write_rate_limit() -> tuple[dict, int] | None:
    now = time.time()
    client_ip = _client_ip()
    recent_hits = [
        hit
        for hit in RATE_LIMIT_BUCKETS.get(client_ip, [])
        if now - hit < RATE_LIMIT_WINDOW_SECONDS
    ]
    RATE_LIMIT_BUCKETS[client_ip] = recent_hits
    if len(recent_hits) >= RATE_LIMIT_WRITE_REQUESTS:
        return {"ok": False, "error": "Muitas requisicoes. Tente novamente em instantes."}, 429
    recent_hits.append(now)
    RATE_LIMIT_BUCKETS[client_ip] = recent_hits
    return None


def _is_valid_hex_id(value: str) -> bool:
    return bool(HEX_ID_RE.fullmatch(value))


def _is_api_request() -> bool:
    return request.path.startswith("/uploads") or request.path.startswith("/comments") or request.path in {"/upload", "/auth/status"}


def _require_delete_token() -> tuple[dict, int] | None:
    if not ADMIN_DELETE_TOKEN:
        return None
    provided_token = request.headers.get("X-Admin-Token", "").strip()
    if provided_token != ADMIN_DELETE_TOKEN:
        return {"ok": False, "error": "Nao autorizado."}, 403
    return None


def _is_authenticated() -> bool:
    return session.get("authenticated") is True


def _password_matches(password: str) -> bool:
    if ADMIN_PASSWORD_HASH:
        return check_password_hash(ADMIN_PASSWORD_HASH, password)
    if ADMIN_PASSWORD:
        return password == ADMIN_PASSWORD
    return False


@app.before_request
def require_login():
    endpoint = request.endpoint or ""
    if endpoint in PUBLIC_ENDPOINTS:
        return None

    if request.path.startswith("/static/"):
        return None

    if _is_authenticated():
        return None

    if _is_api_request():
        return jsonify({"ok": False, "error": "Login obrigatorio."}), 401

    return redirect("/login.html")


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.errorhandler(413)
def file_too_large(_error):
    max_size_mb = round(MAX_UPLOAD_SIZE / (1024 * 1024), 2)
    return jsonify({"ok": False, "error": f"Arquivo excede o limite de {max_size_mb} MB."}), 413


@app.get("/login.html")
def login_page():
    if _is_authenticated():
        return redirect("/")
    return send_from_directory(BASE_DIR, "login.html")


@app.post("/login")
def login():
    limited = _enforce_write_rate_limit()
    if limited:
        payload, status_code = limited
        return jsonify(payload), status_code

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not ADMIN_USERNAME or not (ADMIN_PASSWORD_HASH or ADMIN_PASSWORD):
        return jsonify({"ok": False, "error": "Login nao configurado no servidor."}), 500
    if username != ADMIN_USERNAME or not _password_matches(password):
        return jsonify({"ok": False, "error": "Usuario ou senha invalidos."}), 401

    session.clear()
    session["authenticated"] = True
    session["username"] = ADMIN_USERNAME
    session.permanent = True
    return jsonify({"ok": True, "username": ADMIN_USERNAME}), 200


@app.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True}), 200


@app.get("/auth/status")
def auth_status():
    return jsonify({"authenticated": _is_authenticated(), "username": session.get("username")}), 200


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "album.html")


@app.get("/album.html")
def album():
    return send_from_directory(BASE_DIR, "album.html")


@app.get("/upload.html")
def upload_page():
    return send_from_directory(BASE_DIR, "upload.html")


@app.get("/carpo/<path:filename>")
def serve_carpo(filename: str):
    return send_from_directory(BASE_DIR / "carpo", filename)


@app.post("/upload")
def upload():
    limited = _enforce_write_rate_limit()
    if limited:
        payload, status_code = limited
        return jsonify(payload), status_code

    username = (request.form.get("usuario") or "").strip()
    custom_date = (request.form.get("data") or "").strip()
    uploaded_file = request.files.get("arquivo")

    if not username:
        return jsonify({"ok": False, "error": "Campo 'usuario' e obrigatorio."}), 400
    if len(username) > 80:
        return jsonify({"ok": False, "error": "Campo 'usuario' excede o limite permitido."}), 400
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo para upload."}), 400
    if not _is_allowed(uploaded_file.filename, uploaded_file.mimetype):
        return jsonify({"ok": False, "error": "Tipo de arquivo nao permitido."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    if not safe_name:
        return jsonify({"ok": False, "error": "Nome de arquivo invalido."}), 400

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
    limited = _enforce_write_rate_limit()
    if limited:
        payload, status_code = limited
        return jsonify(payload), status_code
    if not _is_valid_hex_id(photo_id):
        return jsonify({"ok": False, "error": "Identificador invalido."}), 400

    forbidden = _require_delete_token()
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    entries = _load_metadata()
    photo_to_delete = None

    for entry in entries:
        if entry["id"] == photo_id:
            photo_to_delete = entry
            break

    if not photo_to_delete:
        return jsonify({"ok": False, "error": "Foto nao encontrada"}), 404

    file_path = UPLOAD_DIR / photo_to_delete["arquivo_salvo"]
    if file_path.exists():
        file_path.unlink()

    entries = [e for e in entries if e["id"] != photo_id]
    _save_metadata(entries)

    return jsonify({"ok": True, "message": "Foto deletada com sucesso"}), 200


@app.get("/comments/<photo_id>")
def get_comments(photo_id: str):
    if not _is_valid_hex_id(photo_id):
        return jsonify({"ok": False, "error": "Identificador invalido."}), 400
    comments = _load_comments()
    photo_comments = comments.get(photo_id, [])
    return jsonify(photo_comments), 200


@app.post("/comments")
def add_comment():
    limited = _enforce_write_rate_limit()
    if limited:
        payload, status_code = limited
        return jsonify(payload), status_code

    data = request.get_json(silent=True) or {}
    photo_id = (data.get("photo_id") or "").strip()
    usuario = (data.get("usuario") or "").strip()
    texto = (data.get("texto") or "").strip()

    if not photo_id or not usuario or not texto:
        return jsonify({"ok": False, "error": "Campos obrigatorios faltando"}), 400
    if not _is_valid_hex_id(photo_id):
        return jsonify({"ok": False, "error": "Identificador invalido."}), 400
    if len(usuario) > 80 or len(texto) > MAX_COMMENT_LENGTH:
        return jsonify({"ok": False, "error": "Comentario excede o limite permitido."}), 400

    comment = {
        "id": uuid4().hex,
        "usuario": usuario,
        "texto": texto,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    comments = _load_comments()
    if photo_id not in comments:
        comments[photo_id] = []

    comments[photo_id].append(comment)
    _save_comments(comments)

    return jsonify({"ok": True, "comment": comment}), 201


@app.delete("/comments/<comment_id>")
def delete_comment(comment_id: str):
    limited = _enforce_write_rate_limit()
    if limited:
        payload, status_code = limited
        return jsonify(payload), status_code
    if not _is_valid_hex_id(comment_id):
        return jsonify({"ok": False, "error": "Identificador invalido."}), 400

    forbidden = _require_delete_token()
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    comments = _load_comments()
    for photo_id in comments:
        comments[photo_id] = [c for c in comments[photo_id] if c["id"] != comment_id]

    _save_comments(comments)
    return jsonify({"ok": True, "message": "Comentario deletado"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
