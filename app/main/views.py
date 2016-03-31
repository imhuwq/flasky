from datetime import datetime
from flask import render_template
from . import main
from flask.ext.login import login_required
from ..decorators import permission_required, admin_required
from ..models import Permission


@main.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/admin')
@login_required
@admin_required
def admin():
    return "This is a administrator only page."


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderator():
    return "This is a moderator only page"
