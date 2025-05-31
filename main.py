from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from functools import wraps
from flask import abort
from datetime import date
from flask_gravatar import Gravatar
## user can sign up in gravatar site and get a an avatar based on their email so each email has specific avatar
## but if they don't sign up, site will show the default (default parameter in Gravatar class)

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar= Gravatar(
    app,
    size= 100,
    rating= "g",
    default= "retro",
    force_default= False,
    force_lower= False,
    use_ssl= False,
    base_url= None,
)
##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIG MY LOGIN_MANAGER
login_manager= LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

##CONFIGURE TABLES
### three important attributes for UserMixin : is_active, is_authenticated and is_anonymous
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id= db.Column(db.Integer, primary_key= True)
    name= db.Column(db.String, nullable= False)
    email= db.Column(db.String, nullable= False, unique= True)
    password= db.Column(db.String, nullable= False)

    ## posts is a fake column which is equal to list of all objects from BlogPost
    posts= relationship("BlogPost", back_populates= "author")

    comments= relationship("Comment", back_populates= "comment_author")

with app.app_context():
    db.create_all()


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String, nullable= False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    ## author is a fake column which is equal to the object of User
    author = relationship("User", back_populates="posts")

    comments= relationship("Comment", back_populates= "parent_post")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
with app.app_context():
    db.create_all()


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id= db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post= relationship("BlogPost", back_populates= "comments")

with app.app_context():
    db.create_all()

## correct way
def admin_only(f):
    @wraps(f)
    def function_decorated(*args, **kwargs):
        if current_user.is_anonymous or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return function_decorated


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    if current_user.is_authenticated:
        user_id= current_user.id
    else:
        user_id= 2
    return render_template("index.html", all_posts=posts, logged_in= current_user.is_authenticated, user= user_id)


@app.route("/post/<int:post_id>", methods= ["POST", "GET"])
def show_post(post_id):
    form= CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("you need to login or register to comment")
            return redirect(url_for("login"))
        new_comment= Comment(
            text= form.comment.data,
            comment_author= current_user,
            parent_post= requested_post,
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, form= form, logged_in= current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("about.html", logged_in= current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in= current_user.is_authenticated)

## structure of @admin_only is like the @login_required
## @login_required does not let unauthenticated users to access the route by typing in the url
## but @admin_only, in addition to unauthenticated users,
## does not allow users with the id rather than 1 to access the route by typing in the url
## If I enter website without login, and add the url of add_new_post to the url,
## I encounter the error of unauthorized, not forbidden(403), because the @login_required overrides the @admin_only
@app.route("/new-post", methods= ["POST", "GET"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author= current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in= current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods= ["POST", "GET"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, logged_in= current_user.is_authenticated)


@app.route("/delete/<int:post_id>", methods= ["POST", "GET"])
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route('/register', methods= ["POST", "GET"])
def register():
    register_form= RegisterForm()
    if register_form.validate_on_submit():
        if User.query.filter_by(email= register_form.email.data).first():
            flash("Email already exist, please login instead")
            return redirect(url_for("login"))
        hash_salted_password= generate_password_hash(
            password= register_form.password.data,
            method= "pbkdf2:sha256",
            salt_length= 8,
        )
        new_user= User(
            name= register_form.name.data,
            email= register_form.email.data,
            password= hash_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form= register_form, logged_in= current_user.is_authenticated)

@app.route('/login', methods= ["POST", "GET"])
def login():
    login_form= LoginForm()
    if login_form.validate_on_submit():
        entered_email= login_form.email.data
        entered_password= login_form.password.data
        user= User.query.filter_by(email= entered_email).first()
        if not user:
            flash("Email does not exist, please try existing email")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, entered_password):
            flash("password is incorrect, please try again")
            return redirect(url_for("login"))
        else:

            login_user(user)

            return redirect(url_for("get_all_posts"))
    return render_template("login.html", form= login_form, logged_in= current_user.is_authenticated)


@app.route('/logout')
def logout():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug= True)
# host='0.0.0.0', port=5000