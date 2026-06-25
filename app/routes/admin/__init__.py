import os
import zipfile
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, Response
)
from flask_login import login_required, current_user
from functools import wraps
from bson import ObjectId

admin_bp = Blueprint('admin', __name__, template_folder='../../templates/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from app.models.template import get_all_templates, get_active_template
    from app.models.category import get_all_categories
    from app.models.post import get_all_posts
    from app.models.user import User

    stats = {
        'templates': len(get_all_templates()),
        'categories': len(get_all_categories()),
        'posts': len(get_all_posts()),
        'users': len(User.get_all()),
        'active_template': get_active_template(),
    }
    return render_template('admin/dashboard.html', stats=stats)


# ─── Templates ────────────────────────────────────────────────────────────────

@admin_bp.route('/templates')
@admin_required
def template_list():
    from app.models.template import get_all_templates
    templates = get_all_templates()
    return render_template('admin/template_list.html', templates=templates)


@admin_bp.route('/templates/upload', methods=['GET', 'POST'])
@admin_required
def template_upload():
    import shutil
    from app.models.template import create_template, save_section
    from app.utils.template_parser import (
        parse_template, extract_global_styles, extract_global_scripts, rewrite_asset_paths
    )
    from app.utils.zip_template import extract_template_zip
    from app.utils.helpers import allowed_file

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        html_content = ''
        asset_folder = None
        new_id = ObjectId()

        file = request.files.get('template_file')
        if file and file.filename and file.filename.lower().endswith('.zip'):
            dest_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'templates', str(new_id))
            try:
                main_html_rel = extract_template_zip(file, dest_folder)
            except (ValueError, zipfile.BadZipFile) as e:
                shutil.rmtree(dest_folder, ignore_errors=True)
                flash(f'Could not read template archive: {e}', 'danger')
                return render_template('admin/template_upload.html')

            asset_folder = f'uploads/templates/{new_id}'
            main_html_path = os.path.join(dest_folder, *main_html_rel.split('/'))
            with open(main_html_path, 'r', encoding='utf-8', errors='replace') as f:
                raw_html = f.read()
            base_url = url_for('static', filename=asset_folder)
            html_content = rewrite_asset_paths(raw_html, base_url, main_html_rel)
        elif file and file.filename and allowed_file(file.filename):
            html_content = file.read().decode('utf-8', errors='replace')
        else:
            html_content = request.form.get('html_content', '').strip()

        if not name:
            flash('Template name is required.', 'danger')
            return render_template('admin/template_upload.html')
        if not html_content:
            flash('Please upload a file or paste HTML content.', 'danger')
            return render_template('admin/template_upload.html')

        global_css = extract_global_styles(html_content)
        global_js = extract_global_scripts(html_content)
        template_id = create_template(name, html_content, global_css, global_js,
                                       asset_folder=asset_folder, template_id=str(new_id))

        sections, updated_html = parse_template(html_content)
        for sec in sections:
            save_section(template_id, sec)

        message = f'Template "{name}" uploaded with {len(sections)} sections extracted.'
        if asset_folder:
            message += ' Linked CSS, JS, and image files from the archive were imported.'
        flash(message, 'success')
        return redirect(url_for('admin.template_sections', template_id=template_id))

    return render_template('admin/template_upload.html')


@admin_bp.route('/templates/<template_id>/activate', methods=['POST'])
@admin_required
def template_activate(template_id):
    from app.models.template import activate_template
    activate_template(template_id)
    flash('Template activated successfully.', 'success')
    return redirect(url_for('admin.template_list'))


@admin_bp.route('/templates/<template_id>/delete', methods=['POST'])
@admin_required
def template_delete(template_id):
    from app.models.template import delete_template
    delete_template(template_id)
    flash('Template deleted.', 'success')
    return redirect(url_for('admin.template_list'))


@admin_bp.route('/templates/<template_id>/sections')
@admin_required
def template_sections(template_id):
    from app.models.template import get_template_by_id, get_sections_for_template
    template = get_template_by_id(template_id)
    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('admin.template_list'))
    sections = get_sections_for_template(template_id)
    return render_template('admin/sections_list.html', template=template, sections=sections)


# ─── Sections ─────────────────────────────────────────────────────────────────

@admin_bp.route('/sections/<section_id>/edit', methods=['GET', 'POST'])
@admin_required
def section_edit(section_id):
    from app.models.template import get_section_by_id, update_section, get_template_by_id

    section = get_section_by_id(section_id)
    if not section:
        flash('Section not found.', 'danger')
        return redirect(url_for('admin.template_list'))

    template = get_template_by_id(str(section['template_id']))

    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name', section.get('name', '')),
            'content_en': request.form.get('content_en', ''),
            'content_fa': request.form.get('content_fa', ''),
            'css_en': request.form.get('css_en', ''),
            'css_fa': request.form.get('css_fa', ''),
        }
        update_section(section_id, update_data)
        flash('Section saved successfully.', 'success')
        return redirect(url_for('admin.template_sections', template_id=str(section['template_id'])))

    return render_template('admin/section_edit.html', section=section, template=template)


# ─── Categories ───────────────────────────────────────────────────────────────

@admin_bp.route('/categories')
@admin_required
def category_list():
    from app.models.category import get_all_categories
    all_cats = get_all_categories()
    cat_map = {str(c['_id']): c for c in all_cats}
    top_level = [c for c in all_cats if not c.get('parent_id')]
    children = {}
    for c in all_cats:
        if c.get('parent_id'):
            pid = str(c['parent_id'])
            children.setdefault(pid, []).append(c)
    return render_template('admin/category_list.html',
                           top_level=top_level, children=children, cat_map=cat_map)


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def category_create():
    from app.models.category import create_category, get_all_categories
    if request.method == 'POST':
        name_en = request.form.get('name_en', '').strip()
        name_fa = request.form.get('name_fa', '').strip()
        parent_id = request.form.get('parent_id') or None
        desc_en = request.form.get('description_en', '').strip()
        desc_fa = request.form.get('description_fa', '').strip()
        order = int(request.form.get('order', 0))

        if not name_en:
            flash('English name is required.', 'danger')
        else:
            create_category(name_en, name_fa, parent_id, desc_en, desc_fa, order)
            flash('Category created successfully.', 'success')
            return redirect(url_for('admin.category_list'))

    all_cats = get_all_categories()
    return render_template('admin/category_form.html', category=None, all_cats=all_cats, action='create')


@admin_bp.route('/categories/<cat_id>/edit', methods=['GET', 'POST'])
@admin_required
def category_edit(cat_id):
    from app.models.category import get_category_by_id, update_category, get_all_categories
    category = get_category_by_id(cat_id)
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('admin.category_list'))

    if request.method == 'POST':
        data = {
            'name_en': request.form.get('name_en', '').strip(),
            'name_fa': request.form.get('name_fa', '').strip(),
            'description_en': request.form.get('description_en', '').strip(),
            'description_fa': request.form.get('description_fa', '').strip(),
            'order': int(request.form.get('order', 0)),
            'is_active': bool(request.form.get('is_active')),
        }
        parent_id = request.form.get('parent_id') or None
        if parent_id and parent_id != cat_id:
            data['parent_id'] = ObjectId(parent_id)
        else:
            data['parent_id'] = None

        if not data['name_en']:
            flash('English name is required.', 'danger')
        else:
            update_category(cat_id, data)
            flash('Category updated.', 'success')
            return redirect(url_for('admin.category_list'))

    all_cats = [c for c in get_all_categories() if str(c['_id']) != cat_id]
    return render_template('admin/category_form.html', category=category, all_cats=all_cats, action='edit')


@admin_bp.route('/categories/<cat_id>/delete', methods=['POST'])
@admin_required
def category_delete(cat_id):
    from app.models.category import delete_category
    delete_category(cat_id)
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.category_list'))


# ─── Posts ────────────────────────────────────────────────────────────────────

@admin_bp.route('/posts')
@admin_required
def post_list():
    from app.models.post import get_all_posts
    from app.models.category import get_category_by_id
    posts = get_all_posts()
    for p in posts:
        if p.get('category_id'):
            p['_category'] = get_category_by_id(str(p['category_id']))
    return render_template('admin/post_list.html', posts=posts)


@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@admin_required
def post_create():
    from app.models.post import create_post
    from app.models.category import get_all_categories

    if request.method == 'POST':
        data = {
            'title_en': request.form.get('title_en', '').strip(),
            'title_fa': request.form.get('title_fa', '').strip(),
            'excerpt_en': request.form.get('excerpt_en', '').strip(),
            'excerpt_fa': request.form.get('excerpt_fa', '').strip(),
            'content_en': request.form.get('content_en', ''),
            'content_fa': request.form.get('content_fa', ''),
            'custom_css': request.form.get('custom_css', ''),
            'custom_js': request.form.get('custom_js', ''),
            'category_id': request.form.get('category_id') or None,
            'author_id': current_user.id,
            'is_published': bool(request.form.get('is_published')),
        }
        if not data['title_en']:
            flash('English title is required.', 'danger')
        else:
            post_id = create_post(data)
            flash('Post created successfully.', 'success')
            return redirect(url_for('admin.post_list'))

    all_cats = get_all_categories()
    return render_template('admin/post_form.html', post=None, all_cats=all_cats, action='create')


@admin_bp.route('/posts/<post_id>/edit', methods=['GET', 'POST'])
@admin_required
def post_edit(post_id):
    from app.models.post import get_post_by_id, update_post
    from app.models.category import get_all_categories

    post = get_post_by_id(post_id)
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('admin.post_list'))

    if request.method == 'POST':
        data = {
            'title_en': request.form.get('title_en', '').strip(),
            'title_fa': request.form.get('title_fa', '').strip(),
            'excerpt_en': request.form.get('excerpt_en', '').strip(),
            'excerpt_fa': request.form.get('excerpt_fa', '').strip(),
            'content_en': request.form.get('content_en', ''),
            'content_fa': request.form.get('content_fa', ''),
            'custom_css': request.form.get('custom_css', ''),
            'custom_js': request.form.get('custom_js', ''),
            'category_id': request.form.get('category_id') or None,
            'is_published': bool(request.form.get('is_published')),
        }
        if not data['title_en']:
            flash('English title is required.', 'danger')
        else:
            update_post(post_id, data)
            flash('Post updated.', 'success')
            return redirect(url_for('admin.post_list'))

    all_cats = get_all_categories()
    return render_template('admin/post_form.html', post=post, all_cats=all_cats, action='edit')


@admin_bp.route('/posts/<post_id>/delete', methods=['POST'])
@admin_required
def post_delete(post_id):
    from app.models.post import delete_post
    delete_post(post_id)
    flash('Post deleted.', 'success')
    return redirect(url_for('admin.post_list'))


@admin_bp.route('/posts/<post_id>/toggle-publish', methods=['POST'])
@admin_required
def post_toggle_publish(post_id):
    from app.models.post import get_post_by_id, update_post
    post = get_post_by_id(post_id)
    if post:
        update_post(post_id, {'is_published': not post.get('is_published', False)})
        flash('Post publish status updated.', 'success')
    return redirect(url_for('admin.post_list'))


# ─── Users ────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def user_list():
    from app.models.user import User
    users = User.get_all()
    return render_template('admin/user_list.html', users=users)
