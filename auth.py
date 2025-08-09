from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from passlib.hash import bcrypt
from db import execute_query, execute_insert

def init_auth(app):
    pass

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,), dictionary=True
        )
        if user and bcrypt.verify(password, user[0]['password_hash']):
            session['user_id'] = user[0]['id']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth_login.html')

@auth_bp.route('/auth/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))