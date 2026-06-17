from datetime import datetime
from bson import ObjectId
from app.extensions import mongo


def create_template(name, original_html, global_css='', global_js=''):
    doc = {
        'name': name,
        'original_html': original_html,
        'global_css': global_css,
        'global_js': global_js,
        'is_active': False,
        'created_at': datetime.utcnow(),
    }
    result = mongo.db.site_templates.insert_one(doc)
    return str(result.inserted_id)


def get_all_templates():
    return list(mongo.db.site_templates.find().sort('created_at', -1))


def get_template_by_id(template_id):
    try:
        return mongo.db.site_templates.find_one({'_id': ObjectId(template_id)})
    except Exception:
        return None


def get_active_template():
    return mongo.db.site_templates.find_one({'is_active': True})


def activate_template(template_id):
    mongo.db.site_templates.update_many({}, {'$set': {'is_active': False}})
    mongo.db.site_templates.update_one(
        {'_id': ObjectId(template_id)},
        {'$set': {'is_active': True}}
    )


def delete_template(template_id):
    mongo.db.site_templates.delete_one({'_id': ObjectId(template_id)})
    mongo.db.sections.delete_many({'template_id': ObjectId(template_id)})


def get_sections_for_template(template_id):
    try:
        return list(
            mongo.db.sections.find({'template_id': ObjectId(template_id)}).sort('order', 1)
        )
    except Exception:
        return []


def get_section_by_id(section_id):
    try:
        return mongo.db.sections.find_one({'_id': ObjectId(section_id)})
    except Exception:
        return None


def save_section(template_id, section_data):
    section_data['template_id'] = ObjectId(template_id)
    section_data['created_at'] = datetime.utcnow()
    result = mongo.db.sections.insert_one(section_data)
    return str(result.inserted_id)


def update_section(section_id, update_data):
    update_data['updated_at'] = datetime.utcnow()
    mongo.db.sections.update_one(
        {'_id': ObjectId(section_id)},
        {'$set': update_data}
    )


def assemble_template(template, sections, lang='en'):
    """Reassemble the template HTML with edited section content."""
    from bs4 import BeautifulSoup

    html = template.get('original_html', '')
    soup = BeautifulSoup(html, 'lxml')

    for section in sections:
        sid = section.get('section_id')
        if not sid:
            continue
        el = soup.find(id=sid)
        if el:
            content_key = f'content_{lang}'
            content = section.get(content_key) or section.get('content_en', '')
            css_key = f'css_{lang}'
            css = section.get(css_key) or section.get('css_en', '')
            if content:
                el.clear()
                inner = BeautifulSoup(content, 'lxml')
                body = inner.find('body')
                if body:
                    for child in body.children:
                        el.append(child.__copy__() if hasattr(child, '__copy__') else child)
                else:
                    el.append(inner)
            if css:
                existing_style = el.get('style', '')
                el['style'] = existing_style

    # Inject custom CSS blocks
    style_tag = soup.new_tag('style')
    css_parts = [template.get('global_css', '')]
    for section in sections:
        css_key = f'css_{lang}'
        css = section.get(css_key) or section.get('css_en', '')
        if css:
            sid = section.get('section_id', '')
            css_parts.append(f'/* Section: {sid} */\n{css}')
    style_tag.string = '\n'.join(filter(None, css_parts))

    head = soup.find('head')
    if head:
        head.append(style_tag)

    # Inject JS
    if template.get('global_js'):
        script_tag = soup.new_tag('script')
        script_tag.string = template['global_js']
        body = soup.find('body')
        if body:
            body.append(script_tag)

    return str(soup)
