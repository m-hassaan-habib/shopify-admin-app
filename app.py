from flask import Flask, redirect, url_for, session, g, abort, request
from config import Config
from db import get_db_connection
from auth import init_auth, require_login, auth_bp
from blueprints import connect, dashboard, orders, analytics, admin, documents
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
init_auth(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True


ALLOWED_HOSTS = {"localhost", "127.0.0.1", ".ngrok-free.app"}


app.register_blueprint(auth_bp)
app.register_blueprint(connect.blueprint)
app.register_blueprint(dashboard.blueprint)
app.register_blueprint(orders.blueprint)
app.register_blueprint(analytics.blueprint)
app.register_blueprint(admin.blueprint)
app.register_blueprint(documents.blueprint)

@app.before_request
def load_user():
    g.user = None
    if 'user_id' in session:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            g.user = cursor.fetchone()

@app.route('/')
@require_login
def index():
    return redirect(url_for('dashboard.index'))


@app.before_request
def _host_guard():
    host = request.host.split(":")[0]
    if host == "localhost" or host == "127.0.0.1":
        return
    if any(host.endswith(suf.lstrip(".")) for suf in ALLOWED_HOSTS if suf.startswith(".")):
        return
    if host in ALLOWED_HOSTS:
        return
    abort(403)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
