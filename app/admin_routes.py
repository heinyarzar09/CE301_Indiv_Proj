from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import User, Recipe, Post
from app.forms import RegistrationForm, ResetPasswordForm, PostForm

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    return render_template('admin_dashboard.html')

@admin.route('/admin/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    users = User.query.all()
    return render_template('admin_manage_users.html', users=users)

@admin.route('/admin/manage_recipes')
@login_required
def manage_recipes():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    recipes = Recipe.query.all()
    return render_template('admin_manage_recipes.html', recipes=recipes)

@admin.route('/admin/manage_posts')
@login_required
def manage_posts():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    posts = Post.query.all()
    return render_template('admin_manage_posts.html', posts=posts)

@admin.route('/admin/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    return render_template('admin_settings.html')

@admin.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_password(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Password has been updated!', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin_reset_password.html', form=form, user=user)

@admin.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def admin_delete_recipe(recipe_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe has been deleted!', 'success')
    return redirect(url_for('admin.manage_recipes'))

@admin.route('/admin/delete_post/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted!', 'success')
    return redirect(url_for('admin.manage_posts'))

@admin.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
def admin_add_post():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.index'))
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post has been created!', 'success')
        return redirect(url_for('admin.manage_posts'))
    return render_template('admin_add_post.html', form=form)
