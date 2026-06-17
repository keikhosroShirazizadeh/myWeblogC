import os
from flask import session
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'html', 'htm', 'css', 'js', 'zip', 'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, subfolder, upload_folder):
    filename = secure_filename(file.filename)
    dest = os.path.join(upload_folder, subfolder, filename)
    file.save(dest)
    return filename


def get_lang():
    return session.get('lang', 'en')


def t(en_text, fa_text):
    """Return the text in the current session language."""
    if get_lang() == 'fa':
        return fa_text or en_text
    return en_text or fa_text


def format_datetime(dt, fmt='%Y-%m-%d %H:%M'):
    if dt:
        return dt.strftime(fmt)
    return ''
