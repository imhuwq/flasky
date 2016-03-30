from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from ..models import User


class LoginFrom(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Keep Logged in')
    submit = SubmitField('Login')


class RegisterForm(Form):
    email = StringField('Email used to log in', validators=[DataRequired(), Length(1, 64), Email()])
    name = StringField('Nickname makes you unique', validators=[DataRequired(), Length(3, 12),
                                                                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                                       'Username contains only letters,'
                                                                       'numbers and dots and underscores')])
    password = PasswordField('Password used to log in', validators=[DataRequired(),
                                                                    Length(6, 18, message='Password should be'
                                                                                          ' 6-18 at length')])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email has been registered before.')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('This nickname has been taken.')


class ChemailForm(Form):
    old_email = StringField('Your old email address', validators=[DataRequired(), Length(1, 64), Email()])
    new_email = StringField('Your new email address', validators=[DataRequired(), Length(1, 64), Email()])

    def validate_new_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email is in use. Please choose another email.')

    submit = SubmitField('Update')


class ChnameForm(Form):
    old_name = StringField('Old Name', validators=[DataRequired(), Length(3, 12),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'Username contains only letters, '
                                                          'numbers and dots and underscores')])
    new_name = StringField('New Name', validators=[DataRequired(), Length(3, 12),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'Username contains only letters,'
                                                          'numbers and dots and underscores')])

    def validate_new_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('This name is in use. Please choose another name.')

    submit = SubmitField('Update')


class ChpasswdForm(Form):
    old_password = PasswordField('Old Password', validators=[DataRequired(),
                                                             Length(6, 18, message='Password should be'
                                                                                   ' 6-18 at length')])
    password = PasswordField('New Password', validators=[DataRequired(),
                                                         Length(6, 18, message='Password should be'
                                                                               ' 6-18 at length')])
    submit = SubmitField('Update')


class ResetForm(Form):
    email = StringField('Your email', validators=[DataRequired(), Length(1, 64), Email()])

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError('Invalid email.')
    submit = SubmitField('Reset')


class ResetPasswordForm(Form):
    email = StringField('Your email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password used to log in', validators=[DataRequired(),
                                                                    Length(6, 18, message='Password should be'
                                                                                          ' 6-18 at length')])

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError('Invalid email.')

    submit = SubmitField('Reset')
