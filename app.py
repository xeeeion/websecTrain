
from flask import Flask, make_response, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json, os

app = Flask(__name__, static_folder="static", template_folder="templates")
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])

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

@app.route("/")
@limiter.exempt
def index():
    return render_template("index.html")

@app.route("/api/questions")
def questions():
    topic = request.args.get("topic")
    difficulty = request.args.get("difficulty")
    with open(os.path.join(app.static_folder, "questions.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    if topic and topic != "any":
        data = [q for q in data if q.get("topic") == topic]
    if difficulty and difficulty != "any":
        data = [q for q in data if q.get("difficulty") == difficulty]
    return jsonify(data)

@app.after_request
def no_cache_index(resp):
    if request.path == "/" or request.path.endswith("index.html"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
