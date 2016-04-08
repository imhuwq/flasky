from . import api
from ..models import Post, Comment
from .authentication import auth
from flask import jsonify, current_app, request, url_for


@api.route('/comments/')
@auth.login_required
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAG'],
        error_out=False
    )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page + 1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comments/<int:id>')
@auth.login_required
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.query.paginate(
        page, per_page=['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', page=page + 1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
