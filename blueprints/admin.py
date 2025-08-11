from flask import Blueprint, flash
from passlib.hash import bcrypt
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import execute_insert
from auth import require_login

blueprint = Blueprint('admin', __name__)

def create_admin_user(email, password):
    password_hash = bcrypt.hash(password)
    execute_insert(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
        (email, password_hash)
    )
    print(f"Admin user {email} created.")