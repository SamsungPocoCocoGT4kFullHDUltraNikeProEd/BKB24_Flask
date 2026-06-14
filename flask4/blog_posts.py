from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Post, Category, Tag
from forms import PostForm

posts_bp = Blueprint('posts', __name__)


def check_post_permission(post):
    """Проверка прав на редактирование/удаление поста"""
    return post.author_id == current_user.id or current_user.is_admin


@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Создание нового поста"""
    form = PostForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id,
            category_id=form.category.data,
            is_private=form.is_private.data
        )
        db.session.add(post)
        db.session.flush()

        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        db.session.commit()
        flash('Пост успешно создан!', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('create_post.html', form=form)


@posts_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Редактирование поста"""
    post = Post.query.get_or_404(post_id)

    if not check_post_permission(post):
        flash('У вас нет прав для редактирования этого поста', 'danger')
        return redirect(url_for('index'))

    form = PostForm(obj=post)
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category.data
        post.is_private = form.is_private.data
        post.updated_at = datetime.utcnow()

        post.tags = []
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        db.session.commit()
        flash('Пост обновлен!', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    form.tags.data = [tag.id for tag in post.tags]
    return render_template('edit_post.html', form=form, post=post)


@posts_bp.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):
    """Удаление поста"""
    post = Post.query.get_or_404(post_id)

    if not check_post_permission(post):
        flash('У вас нет прав для удаления этого поста', 'danger')
        return redirect(url_for('index'))

    db.session.delete(post)
    db.session.commit()
    flash('Пост удален', 'success')
    return redirect(url_for('index'))


@posts_bp.route('/my_posts')
@login_required
def my_posts():
    """Мои посты"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author_id=current_user.id) \
        .order_by(Post.created_at.desc()) \
        .paginate(page=page, per_page=10)
    return render_template('my_posts.html', posts=posts)


@posts_bp.route('/toggle_private/<int:post_id>')
@login_required
def toggle_private(post_id):
    """Переключение приватности поста"""
    post = Post.query.get_or_404(post_id)

    if not check_post_permission(post):
        flash('У вас нет прав', 'danger')
        return redirect(url_for('index'))

    post.is_private = not post.is_private
    db.session.commit()

    status = 'приватным' if post.is_private else 'публичным'
    flash(f'Пост стал {status}', 'success')
    return redirect(url_for('post_detail', post_id=post.id))