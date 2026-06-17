from bs4 import BeautifulSoup


SEMANTIC_TAGS = ['header', 'nav', 'main', 'footer', 'section', 'article', 'aside', 'div']


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
