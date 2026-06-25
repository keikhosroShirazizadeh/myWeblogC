import posixpath
import re

from bs4 import BeautifulSoup


SEMANTIC_TAGS = ['header', 'nav', 'main', 'footer', 'section', 'article', 'aside', 'div']

ASSET_TAGS = (
    ('link', 'href'),
    ('script', 'src'),
    ('img', 'src'),
    ('source', 'src'),
    ('video', 'src'),
    ('audio', 'src'),
)

_CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(?!data:|https?:|//)([^'\")]+)\1\s*\)")
_EXTERNAL_PREFIXES = ('http://', 'https://', '//', 'data:', '#', 'mailto:', 'tel:')


def rewrite_asset_paths(html_content, base_url, main_html_relpath):
    """Rewrite relative asset references from an extracted zip template so they
    resolve against base_url (the static folder the archive was extracted into),
    instead of relative to the page the assembled template ends up embedded in.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    base_dir = posixpath.dirname(main_html_relpath.replace('\\', '/'))

    def resolve(path):
        if not path or path.startswith(_EXTERNAL_PREFIXES):
            return path
        joined = posixpath.normpath(posixpath.join(base_dir, path)) if base_dir else posixpath.normpath(path)
        return f"{base_url}/{joined.lstrip('/')}"

    for tag_name, attr in ASSET_TAGS:
        for el in soup.find_all(tag_name):
            value = el.get(attr)
            if value:
                el[attr] = resolve(value)

    for style_tag in soup.find_all('style'):
        if style_tag.string:
            style_tag.string.replace_with(
                _CSS_URL_RE.sub(lambda m: f"url({resolve(m.group(2))})", style_tag.string)
            )

    for el in soup.find_all(style=True):
        el['style'] = _CSS_URL_RE.sub(lambda m: f"url({resolve(m.group(2))})", el['style'])

    return str(soup)


def parse_template(html_content):
    """Parse uploaded HTML and extract all identifiable sections."""
    soup = BeautifulSoup(html_content, 'lxml')

    seen_ids = set()
    sections = []
    order = 0

    # First pass: semantic tags with explicit IDs
    for tag_name in ['header', 'nav', 'main', 'footer', 'section', 'article', 'aside']:
        for el in soup.find_all(tag_name):
            el_id = el.get('id')
            if el_id and el_id not in seen_ids:
                seen_ids.add(el_id)
                sections.append(_build_section(el, el_id, order))
                order += 1

    # Second pass: any tag with an id not yet captured
    for el in soup.find_all(id=True):
        el_id = el.get('id')
        if el_id not in seen_ids:
            seen_ids.add(el_id)
            sections.append(_build_section(el, el_id, order))
            order += 1

    # Third pass: semantic tags without IDs — generate IDs for them
    for tag_name in ['header', 'nav', 'main', 'footer', 'section', 'article', 'aside']:
        tag_counter = 1
        for el in soup.find_all(tag_name):
            if not el.get('id'):
                generated_id = f'{tag_name}-auto-{tag_counter}'
                el['id'] = generated_id
                seen_ids.add(generated_id)
                sections.append(_build_section(el, generated_id, order))
                order += 1
                tag_counter += 1

    return sections, str(soup)


def _build_section(el, section_id, order):
    name = section_id.replace('-', ' ').replace('_', ' ').title()
    inner_html = el.decode_contents()
    return {
        'section_id': section_id,
        'tag_name': el.name,
        'name': name,
        'original_html': str(el),
        'content_en': inner_html,
        'content_fa': '',
        'css_en': '',
        'css_fa': '',
        'order': order,
    }


def extract_global_styles(html_content):
    """Extract all <style> tag contents from the template."""
    soup = BeautifulSoup(html_content, 'lxml')
    parts = []
    for tag in soup.find_all('style'):
        if tag.string:
            parts.append(tag.string)
    return '\n'.join(parts)


def extract_global_scripts(html_content):
    """Extract all inline <script> contents (no src attribute)."""
    soup = BeautifulSoup(html_content, 'lxml')
    parts = []
    for tag in soup.find_all('script', src=False):
        if tag.string:
            parts.append(tag.string)
    return '\n'.join(parts)
