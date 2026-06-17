from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session, Response, abort
)
from flask_login import login_required, current_user

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    from app.models.template import get_active_template, get_sections_for_template, assemble_template
    from app.models.post import get_recent_posts
    from app.models.category import get_menu_categories

    lang = session.get('lang', 'en')
    active = get_active_template()
    recent_posts = get_recent_posts(6)

    if not active:
        return render_template('public/no_template.html', recent_posts=recent_posts)

    sections = get_sections_for_template(str(active['_id']))
    assembled_html = assemble_template(active, sections, lang)

    # Pass rendered HTML as a context variable for embedding in layout
    return render_template('public/home.html',
                           assembled_html=assembled_html,
                           recent_posts=recent_posts,
                           lang=lang)


@public_bp.route('/post/<slug>')
def post_detail(slug):
    from app.models.post import get_post_by_slug
    from app.models.category import get_category_by_id
    from app.models.template import get_active_template, get_sections_for_template

    lang = session.get('lang', 'en')
    post = get_post_by_slug(slug)
    if not post:
        abort(404)

    category = get_category_by_id(str(post['category_id'])) if post.get('category_id') else None
    active = get_active_template()
    footer_html = ''
    header_html = ''

    if active:
        sections = get_sections_for_template(str(active['_id']))
        for sec in sections:
            if sec.get('tag_name') == 'footer':
                content = sec.get(f'content_{lang}') or sec.get('content_en', '')
                footer_html = f'<footer id="{sec["section_id"]}">{content}</footer>'
                break
        for sec in sections:
            if sec.get('tag_name') == 'header':
                content = sec.get(f'content_{lang}') or sec.get('content_en', '')
                header_html = f'<header id="{sec["section_id"]}">{content}</header>'
                break

    return render_template('public/post.html',
                           post=post,
                           category=category,
                           header_html=header_html,
                           footer_html=footer_html,
                           lang=lang)


@public_bp.route('/category/<slug>')
def category_posts(slug):
    from app.models.category import get_category_by_slug
    from app.models.post import get_posts_by_category

    lang = session.get('lang', 'en')
    category = get_category_by_slug(slug)
    if not category:
        abort(404)

    posts = get_posts_by_category(str(category['_id']))
    return render_template('public/category.html', category=category, posts=posts, lang=lang)


@public_bp.route('/profile')
@login_required
def profile():
    return render_template('public/profile.html')


@public_bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    profile_data = {
        'first_name': request.form.get('first_name', '').strip(),
        'last_name': request.form.get('last_name', '').strip(),
        'bio_en': request.form.get('bio_en', '').strip(),
        'bio_fa': request.form.get('bio_fa', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'avatar': current_user.profile.get('avatar', ''),
    }

    # Handle avatar upload
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename:
        from app.utils.helpers import allowed_file, save_uploaded_file
        from flask import current_app
        if allowed_file(avatar_file.filename):
            filename = save_uploaded_file(avatar_file, 'avatars', current_app.config['UPLOAD_FOLDER'])
            profile_data['avatar'] = filename

    current_user.update_profile(profile_data)
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('public.profile'))


@public_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'danger')
    elif len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
    elif new_pw != confirm_pw:
        flash('Passwords do not match.', 'danger')
    else:
        current_user.change_password(new_pw)
        flash('Password changed successfully.', 'success')

    return redirect(url_for('public.profile'))
