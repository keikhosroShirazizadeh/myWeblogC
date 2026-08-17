from datetime import datetime
from bson import ObjectId
from app.extensions import mongo


def create_menu_item(data):
    doc = {
        'title_en': data.get('title_en', ''),
        'title_fa': data.get('title_fa', ''),
        'link_type': data.get('link_type', 'custom'),  # 'custom' or 'category'
        'category_id': ObjectId(data['category_id']) if data.get('category_id') else None,
        'url': data.get('url', '').strip(),
        'parent_id': ObjectId(data['parent_id']) if data.get('parent_id') else None,
        'order': data.get('order', 0),
        'open_new_tab': data.get('open_new_tab', False),
        'is_active': data.get('is_active', True),
        'created_at': datetime.utcnow(),
    }
    result = mongo.db.menu_items.insert_one(doc)
    return str(result.inserted_id)


def get_all_menu_items():
    return list(mongo.db.menu_items.find().sort('order', 1))


def get_menu_item_by_id(item_id):
    try:
        return mongo.db.menu_items.find_one({'_id': ObjectId(item_id)})
    except Exception:
        return None


def update_menu_item(item_id, data):
    data['updated_at'] = datetime.utcnow()
    if 'category_id' in data:
        data['category_id'] = ObjectId(data['category_id']) if data['category_id'] else None
    if 'parent_id' in data:
        data['parent_id'] = ObjectId(data['parent_id']) if data['parent_id'] else None
    mongo.db.menu_items.update_one({'_id': ObjectId(item_id)}, {'$set': data})


def delete_menu_item(item_id):
    # Re-assign children to top level, like categories
    mongo.db.menu_items.update_many({'parent_id': ObjectId(item_id)}, {'$set': {'parent_id': None}})
    mongo.db.menu_items.delete_one({'_id': ObjectId(item_id)})


def get_top_level_menu_items(active_only=True):
    query = {'parent_id': None}
    if active_only:
        query['is_active'] = True
    return list(mongo.db.menu_items.find(query).sort('order', 1))


def get_submenu_items(parent_id, active_only=True):
    try:
        query = {'parent_id': ObjectId(parent_id)}
        if active_only:
            query['is_active'] = True
        return list(mongo.db.menu_items.find(query).sort('order', 1))
    except Exception:
        return []


def resolve_menu_item_url(item):
    """Return the href for a menu item, resolving category links to their slug URL."""
    if item.get('link_type') == 'category' and item.get('category_id'):
        from app.models.category import get_category_by_id
        from flask import url_for
        cat = get_category_by_id(str(item['category_id']))
        return url_for('public.category_posts', slug=cat['slug']) if cat else '#'
    return item.get('url') or '#'


def get_menu_tree():
    """Return active top-level menu items (with active children), each annotated with 'resolved_url'."""
    top_level = get_top_level_menu_items()
    tree = []
    for item in top_level:
        item['resolved_url'] = resolve_menu_item_url(item)
        children = get_submenu_items(str(item['_id']))
        for child in children:
            child['resolved_url'] = resolve_menu_item_url(child)
        tree.append({'item': item, 'children': children})
    return tree
