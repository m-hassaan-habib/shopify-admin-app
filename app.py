from flask import Flask, redirect, url_for, session, g
from config import Config
from db import get_db_connection
from auth import init_auth, require_login, auth_bp
from blueprints import connect, dashboard, orders, analytics, admin
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
init_auth(app)

app.register_blueprint(auth_bp)
app.register_blueprint(connect.blueprint)
app.register_blueprint(dashboard.blueprint)
app.register_blueprint(orders.blueprint)
app.register_blueprint(analytics.blueprint)
app.register_blueprint(admin.blueprint)

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

if __name__ == '__main__':
    app.run()