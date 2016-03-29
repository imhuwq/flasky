from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required
from . import auth
from ..models import User
from .forms import LoginFrom, RegisterForm
from .. import db
from .._email import send_email


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginFrom()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('You have not registered. Would you register now?')
            return redirect(url_for('auth.register'))
        elif user.verify_password(form.password.data):
            login_user(user, form.remember.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password!')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have logged out')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register(email=None, password=None):
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name=form.name.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        token = user.generate_confirmation_token()
        send_email(form.email.data, 'Acount Confirmation', 'auth/mail/confirm',
                   user=user, token=token)
        flash('You have successfully signed up.'
              'But you should confirm your account in your email')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Ths account has already been confirmed')
    elif current_user.confirm_token(token):
        flash('You have confirmed your account')
    else:
        flash('The confirmation link is invalid or expired')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated\
            and not current_user.confirmed\
            and request.endpoint[:5] != 'auth.':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Account Confirmation', 'auth/mail/confirm',
               user=current_user, token=token)
    flash('We have resent your a confirmation email')
    return redirect(url_for('main.index'))
