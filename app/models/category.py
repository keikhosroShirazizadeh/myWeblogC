from datetime import datetime
from bson import ObjectId
from app.extensions import mongo
import re


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text


def create_category(name_en, name_fa, parent_id=None, description_en='', description_fa='', order=0):
    slug = slugify(name_en)
    base_slug = slug
    counter = 1
    while mongo.db.categories.count_documents({'slug': slug}) > 0:
        slug = f'{base_slug}-{counter}'
        counter += 1

    doc = {
        'name_en': name_en,
        'name_fa': name_fa,
        'slug': slug,
        'parent_id': ObjectId(parent_id) if parent_id else None,
        'description_en': description_en,
        'description_fa': description_fa,
        'order': order,
        'is_active': True,
        'created_at': datetime.utcnow(),
    }
    result = mongo.db.categories.insert_one(doc)
    return str(result.inserted_id)


def get_all_categories():
    return list(mongo.db.categories.find().sort('order', 1))


def get_category_by_id(cat_id):
    try:
        return mongo.db.categories.find_one({'_id': ObjectId(cat_id)})
    except Exception:
        return None


def get_category_by_slug(slug):
    return mongo.db.categories.find_one({'slug': slug, 'is_active': True})


def get_top_level_categories():
    return list(mongo.db.categories.find({'parent_id': None, 'is_active': True}).sort('order', 1))


def get_subcategories(parent_id):
    try:
        return list(mongo.db.categories.find({'parent_id': ObjectId(parent_id), 'is_active': True}).sort('order', 1))
    except Exception:
        return []


def get_menu_categories():
    """Return categories tree for navigation menu."""
    top_level = get_top_level_categories()
    result = []
    for cat in top_level:
        subs = get_subcategories(str(cat['_id']))
        result.append({'category': cat, 'subcategories': subs})
    return result


def update_category(cat_id, data):
    data['updated_at'] = datetime.utcnow()
    mongo.db.categories.update_one({'_id': ObjectId(cat_id)}, {'$set': data})


def delete_category(cat_id):
    # Re-assign children to top level
    mongo.db.categories.update_many({'parent_id': ObjectId(cat_id)}, {'$set': {'parent_id': None}})
    # Re-assign posts
    mongo.db.posts.update_many({'category_id': ObjectId(cat_id)}, {'$set': {'category_id': None}})
    mongo.db.categories.delete_one({'_id': ObjectId(cat_id)})
