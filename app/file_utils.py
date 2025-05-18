import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def unique_filename(filename: str) -> str:
    upload_dir = current_app.config['UPLOAD_FOLDER']
    base, ext = os.path.splitext(secure_filename(filename))
    candidate = f"{base}{ext}"
    while os.path.exists(os.path.join(upload_dir, candidate)):
        candidate = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
    return candidate
