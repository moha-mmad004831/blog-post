from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name= StringField(label= "name", validators= [DataRequired()])
    email= StringField(label= "email", validators= [DataRequired(), Email()])
    password= PasswordField(label= "password", validators= [DataRequired()])
    submit= SubmitField(label= "submit")


class LoginForm(FlaskForm):
    email= StringField(label= "email", validators= [DataRequired(), Email()])
    password= PasswordField(label= "password", validators= [DataRequired()])
    submit= SubmitField(label= "submit")


class CommentForm(FlaskForm):
    comment= CKEditorField(label= "comment", validators= [DataRequired()])
    submit= SubmitField(label= "submit")