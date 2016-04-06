from flask import render_template, abort, flash, url_for, redirect, request, current_app, make_response
from . import main
from flask.ext.login import login_required, current_user
from ..decorators import permission_required, admin_required
from ..models import User, Permission, Post
from .forms import AdminChprofileForm, PostForm
from .. import db


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and\
       form.validate_on_submit():
        post = Post(
                    body=form.body.data,
                    author=current_user._get_current_object()
                    )
        db.session.add(post)
        return redirect(url_for('main.index'))
    show_followed = False
    show_mine = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
        show_mine = bool(request.cookies.get('show_mine', ''))
    if show_followed:
        query = current_user.followed_posts
    elif show_mine:
        query = current_user.posts
    else:
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, show_mine=show_mine,
                           pagination=pagination)


@main.route('/user/<name>/profile/')
def profile(name):
    u = User.query.filter_by(name=name).first()
    if u is None:
        abort(404)
    return render_template('profile.html', user=u)


@main.route('/user/<name>/follow/<uname>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(name, uname):
    u = User.query.filter_by(name=uname).first()
    if u is None:
        flash('Invalid User')
        return redirect(request.referrer or url_for('main.index'))
    if u == current_user:
        flash('You cannot follow yourself')
        return redirect(request.referrer or url_for('main.index'))
    elif current_user.is_following(u):
        flash('You are already following this user')
        return redirect(request.referrer or url_for('main.profile', name=u.name))
    current_user.follow(u)
    flash('You are now following %s' % u.name)
    return redirect(request.referrer or url_for('main.profile', name=u.name))


@main.route('/user/<name>/unfollow/<uname>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(name, uname):
    u = User.query.filter_by(name=uname).first()
    if u is None:
        flash('Invalid User')
        return redirect(request.referrer or url_for('main.index'))
    elif not current_user.is_following(u):
        flash('You are not following this user')
        return redirect(request.referrer or url_for('main.profile', name=u.name))
    current_user.unfollow(u)
    flash('You are now unfollowing %s' % u.name)
    return redirect(request.referrer or url_for('main.profile', name=u.name))


@main.route('/user/<name>/profile/follower')
def follower(name):
    u = User.query.filter_by(name=name).first()
    if u is None:
        flash('Invalid user')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = u.follower.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('follower.html', user=u,
                           title='Followers of',
                           endpoint='main.follower',
                           pagination=pagination,
                           follows=follows)


@main.route('/user/<name>/profile/followed')
def followed(name):
    u = User.query.filter_by(name=name).first()
    if u is None:
        flash('Invalid user')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = u.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWEDS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followed.html', user=u,
                           title='Followed by',
                           endpoint='main.followed',
                           pagination=pagination,
                           follows=follows)


@main.route('/user/<name>/posts')
def posts(name):
    u = User.query.filter_by(name=name).first()
    if u is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(author=u).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('posts.html', user=u, posts=posts,
                           pagination=pagination)


@main.route('/posts/all')
@login_required
def all_posts():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    resp.set_cookie('show_mine', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/posts/followed')
@login_required
def followed_posts():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    resp.set_cookie('show_mine', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/posts/mine')
@login_required
def my_posts():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_mine', '1', max_age=30*24*60*60)
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/post/<int:id>/read')
@main.route('/post/<int:id>')
def post_read(id):
    post = Post.query.get_or_404(id)
    return render_template('post_read.html', posts=[post])


@main.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def post_edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('Post has been republished.')
        return redirect(url_for('main.post_read', id=post.id))
    form.body.data = post.body
    return render_template('post_edit.html', form=form)


@main.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')


@main.route('/admin/user')
@login_required
@admin_required
def user_list():
    us = User.query.order_by(User.id).all()
    return render_template('user_list.html', users=us)


@main.route('/admin/user/<int:u_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user(u_id):
    u = User.query.get_or_404(u_id)
    if u.role_id == 3 and u != current_user:
        flash('You don\'t have the permission to edit another Administrators profile.')
        return redirect(url_for('main.user_list'))
    form = AdminChprofileForm(u)
    if form.validate_on_submit():
        u.email = form.email.data
        u.name = form.name.data
        u.confirmed = form.confirmed.data
        u.role_id = form.role.data
        u.full_name = form.full_name.data
        u.location = form.location.data
        u.about_me = form.about_me.data
        db.session.add(u)
        db.session.commit()
        flash('User profile updated')
        return redirect(url_for('main.index'))
    form.email.data = u.email
    form.name.data = u.name
    form.confirmed.data = u.confirmed
    form.role.data = u.role_id
    form.full_name.data = u.full_name
    form.location.data = u.location
    form.about_me.data = u.about_me
    return render_template('edit_user.html', form=form, user=u)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderator():
    return "This is a moderator only page"


@main.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403
