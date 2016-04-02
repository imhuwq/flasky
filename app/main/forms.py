from flask.ext.wtf import Form
from flask.ext.pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from ..models import User, Role


class AdminChprofileForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    name = StringField('Nickname', validators=[DataRequired(), Length(3, 12),
                                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                      'Username contains only letters,'
                                                      'numbers and dots and underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    full_name = StringField('Full Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')

    def __init__(self, user, *args, **kwargs):
        super(AdminChprofileForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('This email is in use.')

    def validate_name(self, field):
        if field.data != self.user.name and User.query.filter_by(name=field.data).first():
            raise ValidationError('This nickname is in use.')

    def validate_role(self, field):
        if field.data != Role.query.filter_by(name='Administrator').first()\
           and self.user.is_administrator()\
           and len(User.query.filter_by(role_id=3).all()) == 1:
            raise ValidationError('At least one Admin is required to run this site.')
    submit = SubmitField('Update')


class PostForm(Form):
    body = PageDownField('What\'s on your mind ?', validators=[DataRequired()])
    submit = SubmitField('Publish')
