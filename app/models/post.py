from datetime import datetime
from bson import ObjectId
from app.extensions import mongo
import re


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text


def create_post(data):
    slug = slugify(data.get('title_en', 'post'))
    base_slug = slug
    counter = 1
    while mongo.db.posts.count_documents({'slug': slug}) > 0:
        slug = f'{base_slug}-{counter}'
        counter += 1

    doc = {
        'title_en': data.get('title_en', ''),
        'title_fa': data.get('title_fa', ''),
        'slug': slug,
        'excerpt_en': data.get('excerpt_en', ''),
        'excerpt_fa': data.get('excerpt_fa', ''),
        'content_en': data.get('content_en', ''),
        'content_fa': data.get('content_fa', ''),
        'custom_css': data.get('custom_css', ''),
        'custom_js': data.get('custom_js', ''),
        'category_id': ObjectId(data['category_id']) if data.get('category_id') else None,
        'author_id': ObjectId(data['author_id']) if data.get('author_id') else None,
        'is_published': data.get('is_published', False),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    result = mongo.db.posts.insert_one(doc)
    return str(result.inserted_id)


def get_all_posts(published_only=False):
    query = {'is_published': True} if published_only else {}
    return list(mongo.db.posts.find(query).sort('created_at', -1))


def get_post_by_id(post_id):
    try:
        return mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    except Exception:
        return None


def get_post_by_slug(slug):
    return mongo.db.posts.find_one({'slug': slug, 'is_published': True})


def get_posts_by_category(category_id, published_only=True):
    try:
        query = {'category_id': ObjectId(category_id)}
        if published_only:
            query['is_published'] = True
        return list(mongo.db.posts.find(query).sort('created_at', -1))
    except Exception:
        return []


def update_post(post_id, data):
    data['updated_at'] = datetime.utcnow()
    if 'category_id' in data and data['category_id']:
        data['category_id'] = ObjectId(data['category_id'])
    mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': data})


def delete_post(post_id):
    mongo.db.posts.delete_one({'_id': ObjectId(post_id)})


def get_recent_posts(limit=5):
    return list(mongo.db.posts.find({'is_published': True}).sort('created_at', -1).limit(limit))
