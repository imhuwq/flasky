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
    password2 = PasswordField('Confirm your password', validators=[EqualTo('password',
                                                                           message='Password must be match')])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email has been registered before.')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('This nickname has been taken.')
