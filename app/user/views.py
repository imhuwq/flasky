from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required
from . import user
from ..models import User
from .forms import LoginFrom, RegisterForm
from .. import db
from .._email import send_email
import re


@user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginFrom()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u is None:
            flash('You have not registered. Would you register now?')
            return redirect(url_for('user.register'))
        elif u.verify_password(form.password.data):
            login_user(u, form.remember.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password!')
    return render_template('user/login.html', form=form)


@user.route('/logout')
def logout():
    logout_user()
    flash('You have logged out')
    return redirect(url_for('main.index'))


def check_password_security(passwd):
    base = len(passwd)
    factor = 0
    if re.compile(r'[0-9]').search(passwd) is not None:
        factor += 1
    if re.compile(r'[a-z]').search(passwd) is not None:
        factor += 1
    if re.compile(r'[A-Z]').search(passwd) is not None:
        factor += 1
    if re.compile(r'\.|\_').search(passwd) is not None:
        factor += 1
    complexity = base * factor
    if complexity <= 7:
        return 'weak'
    elif complexity <= 25:
        return 'medium'
    elif complexity <= 35:
        return 'strong'
    else:
        return 'very strong'

@user.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        security = check_password_security(form.password.data)
        u = User(email=form.email.data,
                 name=form.name.data,
                 password=form.password.data,
                 password_security = security)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        token = u.generate_confirmation_token()
        send_email(form.email.data, 'Account Confirmation', 'user/mail/confirm',
                   user=u, token=token)
        flash('You have successfully signed up.'
              'But you should confirm your account in your email')
        return redirect(url_for('main.index'))
    return render_template('user/register.html', form=form)


@user.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Ths account has already been confirmed')
    elif current_user.confirm_token(token):
        flash('You have confirmed your account')
    else:
        flash('The confirmation link is invalid or expired')
    return redirect(url_for('main.index'))


@user.before_app_request
def before_request():
    if current_user.is_authenticated\
            and not current_user.confirmed\
            and request.endpoint[:5] != 'user.':
        return redirect(url_for('user.unconfirmed'))


@user.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('user/unconfirmed.html')


@user.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Account Confirmation', 'user/mail/confirm',
               user=current_user, token=token)
    flash('We have resent your a confirmation email')
    return redirect(url_for('main.index'))


@user.route('/profile')
@login_required
def profile():
    u = current_user
    return render_template('user/profile.html', user=u)


@user.route('/chemail')
@login_required
def change_email():
    pass


@user.route('/chname')
@login_required
def change_name():
    pass


@user.route('/privileges')
@login_required
def privileges():
    pass


@user.route('/chpasswd')
@login_required
def change_password():
    pass