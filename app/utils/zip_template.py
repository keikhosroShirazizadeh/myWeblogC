import os
import posixpath
import zipfile

MAIN_HTML_NAMES = ('index.html', 'index.htm')
SKIP_PREFIXES = ('__MACOSX/',)
SKIP_NAMES = ('.DS_Store', 'Thumbs.db')


def extract_template_zip(file_storage, dest_folder):
    """Extract an uploaded template .zip archive into dest_folder.

    Returns the posix-style relative path of the main HTML file to use as the
    template's entry point. Raises ValueError if the archive has no HTML file
    or contains a path that would escape dest_folder.
    """
    os.makedirs(dest_folder, exist_ok=True)
    dest_root = os.path.realpath(dest_folder)

    with zipfile.ZipFile(file_storage) as zf:
        members = []
        for info in zf.infolist():
            name = info.filename.replace('\\', '/')
            if info.is_dir() or name.endswith('/'):
                continue
            if any(name.startswith(p) for p in SKIP_PREFIXES) or os.path.basename(name) in SKIP_NAMES:
                continue

            target = os.path.realpath(os.path.join(dest_folder, name))
            if not (target == dest_root or target.startswith(dest_root + os.sep)):
                raise ValueError(f'Refusing to extract unsafe path in archive: {info.filename}')

            members.append((info, name))

        html_files = [n for _, n in members if n.lower().endswith(('.html', '.htm'))]
        if not html_files:
            raise ValueError('No HTML file found in the uploaded archive.')

        for info, name in members:
            dest_path = os.path.join(dest_folder, name)
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            with zf.open(info) as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())

    for candidate in html_files:
        if posixpath.basename(candidate).lower() in MAIN_HTML_NAMES:
            return candidate
    return min(html_files, key=lambda n: n.count('/'))
