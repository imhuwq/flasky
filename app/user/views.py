from flask import render_template, redirect, request, url_for, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
from . import user
from ..models import User
from .forms import LoginFrom, RegisterForm, ChemailForm, ChnameForm, ChpasswdForm, ResetForm, ResetPasswordForm
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
            session['temp_email'] = form.email.data
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
    # TODO: test if session is every user separately
    if session.get('temp_email'):
        form.email.data = session.get('temp_email')
    if form.validate_on_submit():
        session['temp_email'] = None
        security = check_password_security(form.password.data)
        u = User(email=form.email.data,
                 name=form.name.data,
                 password=form.password.data,
                 password_security=security)
        print(u.role)
        token = u.generate_confirmation_token()
        send_email(form.email.data, 'Account Confirmation', 'user/mail/confirm',
                   user=u, token=token)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash('You have successfully signed up.'
              'But you should confirm your account in your email')
        return redirect(url_for('main.index'))
    return render_template('user/register.html', form=form)


@user.route('/confirm/<action>/<token>')
@login_required
def confirm(action, token):
    u = current_user
    if action == 'register':
        if u.confirmed:
            flash('Ths account has already been confirmed')
        elif u.confirm_token(token):
            flash('You have confirmed your account')
        else:
            flash('The confirmation link is invalid or expired')
        return redirect(url_for('main.index'))
    if action == 'chemail':
        if u.confirm_token(token):
            u.email, u.suspend_email = u.suspend_email, None
            db.add(u)
            db.commit()
            flash('You have successfully updated your email.')
            return redirect(url_for('user.profile'))
    return url_for('main.index')


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


@user.route('/privileges')
@login_required
def privileges():
    return "This page is left for further design."


@user.route('/update/<action>', methods=['GET', 'POST'])
@login_required
def update(action):
    u = current_user
    if action == 'chemail':
        form = ChemailForm()
        form.old_email.data = u.email
        if form.validate_on_submit():
            if form.old_email.data != u.email:
                flash('Invalid old email')
                return redirect(url_for('user.update', action=action))
            u.suspend_email = form.new_email.data
            token = u.generate_confirmation_token()
            send_email(form.new_email.data, 'Account Update', 'user/mail/update',
                       token=token, user=user, action=action)
            db.session.add(u)
            db.session.commit()
            flash('Please check your new email to confirm this update')
            return redirect(url_for('user.profile'))
    elif action == 'chname':
        form = ChnameForm()
        form.old_name.data = u.name
        if form.validate_on_submit():
            u.name = form.new_name.data
            db.session.add(u)
            db.session.commit()
            flash('You have successfully changed your name.')
            return redirect(url_for('user.profile'))
    elif action == 'chpasswd':
        form = ChpasswdForm()
        if form.validate_on_submit():
            u.password = form.password.data
            db.session.add(u)
            db.session.commit()
            flash('You have successfully changed your password.')
            return redirect(url_for('user.profile'))
    return render_template('user/update.html', action=action, form=form)


@user.route('/reset/<action>', methods=['GET', 'POST'])
def reset(action):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        token = u.generate_confirmation_token(600)
        send_email(form.email.data, 'Reset Password Confirmation', 'user/mail/reset',
                   user=u, token=token, action=action)
        flash('An instruction to reset password is sent to your email')
        return redirect(url_for('main.index'))
    return render_template('user/reset.html', form=form, action=action)


@user.route('/reset/<action>/confirm/<token>', methods=['GET', 'POST'])
def reset_confirm(action, token):
    u = current_user
    if action == 'password':
        if not u.is_anonymous:
            return redirect(url_for('main.index'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            u = User.query.filter_by(email=form.email.data).first()
            if u.confirm_token(token):
                u.password = form.password.data
                db.session.add(u)
                db.session.commit()
                flash('You have reset your password')
                return redirect(url_for('user.login'))
            flash('Invalid email')
        return render_template('user/reset.html', form=form)
    return url_for('main.index')
