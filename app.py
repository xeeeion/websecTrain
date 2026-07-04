
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, render_template, jsonify, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import re


def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                os.environ.setdefault(key, value)


load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])
DATA_DIR = os.path.join(app.root_path, "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
MAX_LOGIN_FAILURES = int(os.getenv("MAX_LOGIN_FAILURES", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "10"))
LOGIN_FAILURES = {}

EMPTY_PROGRESS = {"answered": {}, "wrong": [], "attempts": []}

CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",
    "img-src": "'self' data:",
    "connect-src": "'self'",
    "object-src": "'none'",
    "base-uri": "'self'",
    "frame-ancestors": "'none'",
}
CSP_HEADER = "; ".join([f"{k} {v}" for k, v in CSP.items()])

@app.after_request
def set_headers(resp):
    resp.headers["Content-Security-Policy"] = CSP_HEADER
    resp.headers["Referrer-Policy"] = "no-referrer"
    if os.getenv("ENABLE_HSTS", "1") == "1":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    resp.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    resp.headers["Cross-Origin-Resource-Policy"] = "same-site"
    resp.headers["Server"] = "secure"
    return resp

@app.route("/healthz")
def healthz():
    return "ok"


def utc_now():
    return datetime.now(timezone.utc)


def empty_progress():
    return json.loads(json.dumps(EMPTY_PROGRESS))


def read_users():
    ensure_users()
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    return sync_admin_from_env(users)


def write_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def sync_admin_from_env(users):
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        return users
    admin = users.get(admin_username)
    if not admin or admin.get("role") != "admin" or not check_password_hash(admin.get("password_hash", ""), admin_password):
        users[admin_username] = {
            "password_hash": generate_password_hash(admin_password),
            "role": "admin",
            "progress": (admin or {}).get("progress") or empty_progress(),
        }
        write_users(users)
    return users


def ensure_users():
    if os.path.exists(USERS_PATH):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD must be set in .env before first start")
    users = {
        admin_username: {
            "password_hash": generate_password_hash(admin_password),
            "role": "admin",
            "progress": empty_progress(),
        }
    }
    student_username = os.getenv("STUDENT_USERNAME")
    student_password = os.getenv("STUDENT_PASSWORD")
    if student_username and student_password and student_username not in users:
        users[student_username] = {
            "password_hash": generate_password_hash(student_password),
            "role": "user",
            "progress": empty_progress(),
        }
    write_users(users)


def current_user():
    username = session.get("username")
    if not username:
        return None
    users = read_users()
    user = users.get(username)
    if not user:
        session.clear()
        return None
    return {"username": username, "role": user.get("role", "user")}


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "auth_required"}), 401
        return fn(*args, **kwargs)
    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "auth_required"}), 401
        if user.get("role") != "admin":
            return jsonify({"error": "admin_required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def login_key(username):
    return f"{get_remote_address()}:{username.lower()}"


def is_locked(username):
    state = LOGIN_FAILURES.get(login_key(username))
    if not state:
        return False, None
    lock_until = state.get("lock_until")
    if lock_until and lock_until > utc_now():
        return True, lock_until
    if lock_until:
        LOGIN_FAILURES.pop(login_key(username), None)
    return False, None


def record_login_failure(username):
    key = login_key(username)
    state = LOGIN_FAILURES.setdefault(key, {"count": 0, "lock_until": None})
    state["count"] += 1
    if state["count"] >= MAX_LOGIN_FAILURES:
        state["lock_until"] = utc_now() + timedelta(minutes=LOCKOUT_MINUTES)


def clear_login_failures(username):
    LOGIN_FAILURES.pop(login_key(username), None)


def validate_new_user(username, password):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
        return "bad_username"
    if len(password) < 8 or len(password) > 128:
        return "weak_password"
    return None


@app.route("/api/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    validation_error = validate_new_user(username, password)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    users = read_users()
    if username in users:
        return jsonify({"error": "user_exists"}), 409

    users[username] = {
        "password_hash": generate_password_hash(password),
        "role": "user",
        "progress": empty_progress(),
    }
    write_users(users)
    session.clear()
    session["username"] = username
    session.permanent = True
    return jsonify({"username": username, "role": "user"}), 201


@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400

    locked, lock_until = is_locked(username)
    if locked:
        return jsonify({
            "error": "locked",
            "lockedUntil": lock_until.isoformat(),
        }), 429

    users = read_users()
    user = users.get(username)
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        record_login_failure(username)
        return jsonify({"error": "invalid_credentials"}), 401

    clear_login_failures(username)
    session.clear()
    session["username"] = username
    session.permanent = True
    return jsonify({"username": username, "role": user.get("role", "user")})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, **user})


@app.route("/")
@limiter.exempt
def index():
    return render_template("index.html")

def load_content():
    path = os.path.join(app.static_folder, "trainer_content.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_questions(questions):
    topic = request.args.get("topic", "any")
    level = request.args.get("level") or request.args.get("difficulty", "any")
    task_type = request.args.get("type", "any")

    if topic and topic != "any":
        questions = [q for q in questions if q.get("topic") == topic]
    if level and level != "any":
        questions = [q for q in questions if q.get("level") == level]
    if task_type and task_type != "any":
        questions = [q for q in questions if q.get("type") == task_type]
    return questions


@app.route("/api/content")
@require_login
def content():
    payload = load_content()
    payload["questions"] = filter_questions(payload.get("questions", []))
    return jsonify(payload)


@app.route("/api/questions")
@require_login
def questions():
    payload = load_content()
    return jsonify(filter_questions(payload.get("questions", [])))


@app.route("/api/progress", methods=["GET"])
@require_login
def get_progress():
    users = read_users()
    user = users[session["username"]]
    return jsonify(user.get("progress") or empty_progress())


@app.route("/api/progress", methods=["PUT"])
@require_login
def save_progress():
    payload = request.get_json(silent=True) or {}
    progress = {
        "answered": payload.get("answered") if isinstance(payload.get("answered"), dict) else {},
        "wrong": payload.get("wrong") if isinstance(payload.get("wrong"), list) else [],
        "attempts": payload.get("attempts") if isinstance(payload.get("attempts"), list) else [],
    }
    users = read_users()
    users[session["username"]]["progress"] = progress
    write_users(users)
    return jsonify({"ok": True})


@app.route("/api/admin/users")
@require_admin
def admin_users():
    users = read_users()
    return jsonify([
        {
            "username": username,
            "role": user.get("role", "user"),
            "answered": len((user.get("progress") or {}).get("answered", {})),
            "wrong": len((user.get("progress") or {}).get("wrong", [])),
        }
        for username, user in sorted(users.items())
    ])


@app.route("/api/admin/reset-progress", methods=["POST"])
@require_admin
def admin_reset_progress():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    users = read_users()
    if username not in users:
        return jsonify({"error": "unknown_user"}), 404
    users[username]["progress"] = empty_progress()
    write_users(users)
    return jsonify({"ok": True, "username": username})

@app.after_request
def no_cache_index(resp):
    if request.path == "/" or request.path.endswith("index.html") or request.path.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp

ensure_users()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
