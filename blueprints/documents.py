# blueprints/documents.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os, json, time, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import execute_query, execute_insert

blueprint = Blueprint('documents', __name__)

UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads', 'documents')

@blueprint.route('/settings/documents', methods=['GET'])
def docs_page():
    rows = execute_query("SELECT id, doc_type, file_path, is_active, version, uploaded_at, fill_mode, font_name FROM shop_documents ORDER BY uploaded_at DESC", dictionary=True)
    return render_template('documents.html', docs=rows, active_page='documents')


@blueprint.route('/settings/documents', methods=['POST'])
def docs_upload():
    doc_type = request.form.get('doc_type')
    field_map_raw = request.form.get('field_map_json') or ''
    coord_map_raw = request.form.get('coordinate_map_json') or ''
    fill_mode = request.form.get('fill_mode') or 'form'
    font_name = request.form.get('font_name') or None
    f = request.files.get('file')
    if not doc_type or not f:
        flash('Missing type or file', 'danger')
        return redirect(url_for('documents.docs_page'))
    
    os.makedirs(os.path.join(UPLOAD_DIR, doc_type), exist_ok=True)
    fname = secure_filename(f.filename or f'{doc_type}.pdf')
    ts = int(time.time())
    path = os.path.join(UPLOAD_DIR, doc_type, f'{ts}_{fname}')
    f.save(path)
    execute_query("UPDATE shop_documents SET is_active=0 WHERE doc_type=%s AND is_active=1", (doc_type,))
    field_map = None

    if field_map_raw.strip():
        field_map = json.dumps(json.loads(field_map_raw))
    coord_map = None

    if coord_map_raw.strip():
        coord_map = json.dumps(json.loads(coord_map_raw))

    version = (execute_query("SELECT COALESCE(MAX(version),0)+1 FROM shop_documents WHERE doc_type=%s", (doc_type,)) or [(1,)])[0][0]
    
    execute_insert(
            "INSERT INTO shop_documents (doc_type, file_path, is_active, version, fill_mode, font_name, coordinate_map_json, field_map_json) VALUES (%s,%s,1,%s,%s,%s,%s,%s)",
            (doc_type, path, version, fill_mode, font_name, coord_map, field_map)
    )
    
    flash('Uploaded', 'success')
    return redirect(url_for('documents.docs_page'))
