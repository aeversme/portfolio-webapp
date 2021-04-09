from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm
from flask_gravatar import Gravatar
from functools import wraps
import smtplib
from dotenv import load_dotenv
from datetime import date
import os

application = Flask(__name__)
current_year = date.today().year
Bootstrap(application)
ckeditor = CKEditor(application)
load_dotenv()

# App & DB Config
application.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)

login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = 'login'

gravatar = Gravatar(application,
                    size=100,
                    rating='g',
                    default='identicon',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(function):
    @wraps(function)
    def check_user_id(*args, **kwargs):
        if current_user.id != 1:
            abort(403)
        return function(*args, **kwargs)
    return check_user_id


# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship('Comment', back_populates='parent_post')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    comment_author = relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='comments')
    text = db.Column(db.String(1000), nullable=False)


db.create_all()


@application.route('/')
def get_index():
    return render_template('index.html',
                           year=current_year,
                           logged_in=current_user.is_authenticated)


@application.route('/about')
def get_about_page():
    return render_template('about.html',
                           year=current_year,
                           logged_in=current_user.is_authenticated)


@application.route('/projects')
def get_projects():
    return render_template('/projects.html',
                           year=current_year,
                           logged_in=current_user.is_authenticated)


@application.route('/blog')
def get_all_posts():
    blog_posts = db.session.query(BlogPost).all()
    return render_template('blog.html',
                           year=current_year,
                           all_posts=blog_posts,
                           logged_in=current_user.is_authenticated)


@application.route('/register', methods=['GET', 'POST'])
def register_new_user():
    register_form = RegisterForm()
    if request.method == 'POST' and register_form.validate():
        if User.query.filter_by(email=register_form.email.data).first():
            flash('That email is already registered, log in instead!')
            return redirect(url_for('login'))
        else:
            hash_and_salted_password = generate_password_hash(
                password=register_form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User()
            new_user.name = register_form.name.data
            new_user.email = register_form.email.data
            new_user.password = hash_and_salted_password
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('get_all_posts'))

    return render_template("register.html",
                           form=register_form,
                           logged_in=current_user.is_authenticated)


@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_all_posts'))
    login_form = LoginForm()
    if request.method == 'POST' and login_form.validate():
        user = User.query.filter_by(email=login_form.email.data).first()
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, login_form.password.data):
            flash('Incorrect password, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html",
                           form=login_form,
                           logged_in=current_user.is_authenticated)


@application.route('/logout')
def logout():
    logout_user()
    return redirect(request.referrer)


@application.route('/post/<int:post_id>', methods=['GET', 'POST'])
def get_blog_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    if request.method == 'POST' and comment_form.validate():
        if not current_user.is_authenticated:
            flash('You need to login or register to comment.')
            return redirect(url_for('login'))
        else:
            new_comment = Comment(
                post_id=post_id,
                author_id=current_user.id,
                text=comment_form.comment.data
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('get_blog_post', post_id=post_id))
    return render_template('post.html',
                           year=current_year,
                           blog_post=requested_post,
                           form=comment_form,
                           logged_in=current_user.is_authenticated)


@application.route('/make-post', methods=['GET', 'POST'])
@admin_only
def make_post():
    post_form = CreatePostForm()
    if post_form.validate_on_submit():
        new_blog_post = BlogPost(
            title=post_form.title.data,
            subtitle=post_form.subtitle.data,
            date=date.today().strftime('%B %d, %Y'),
            body=post_form.body.data,
            author=current_user,
            img_url=post_form.img_url.data
        )
        db.session.add(new_blog_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template('make-post.html',
                           year=current_year,
                           form=post_form,
                           logged_in=current_user.is_authenticated)


@application.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    selected_post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=selected_post.title,
        subtitle=selected_post.subtitle,
        img_url=selected_post.img_url,
        author=selected_post.author,
        body=selected_post.body
    )
    if edit_form.validate_on_submit():
        selected_post.title = edit_form.title.data
        selected_post.subtitle = edit_form.subtitle.data
        selected_post.body = edit_form.body.data
        selected_post.author = current_user
        selected_post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for('get_blog_post', post_id=selected_post.id))
    return render_template('make-post.html',
                           form=edit_form,
                           is_edit=True,
                           logged_in=current_user.is_authenticated)


@application.route('/delete/<int:post_id>')
@admin_only
def delete(post_id):
    selected_post = BlogPost.query.get(post_id)
    db.session.delete(selected_post)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@application.route('/resume')
def get_resume():
    return render_template('resume.html',
                           year=current_year,
                           logged_in=current_user.is_authenticated)


@application.route('/contact', methods=['GET', 'POST'])
def contact_me():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        # TODO Add a try/except statement here, use 'except SMTPException'
        with smtplib.SMTP('smtp.mail.yahoo.com') as connection:
            connection.starttls()
            connection.login(user=os.getenv('SEND_EMAIL_FROM'), password=os.getenv('PASSWORD'))
            connection.sendmail(
                from_addr=os.getenv('SEND_EMAIL_FROM'),
                to_addrs=os.getenv('SEND_EMAIL_TO'),
                msg=f'Subject: Blog Form Submission\n\n'
                    f'Name: {contact_form.name.data}\n'
                    f'Email: {contact_form.email.data}\n'
                    f'Message: {contact_form.message.data}\n'
            )
        # TODO Should be within the else statement of the try/except
        flash('Your message has been successfully sent. Thanks!')
        return redirect(url_for('contact_me'))
    return render_template('contact.html',
                           year=current_year,
                           form=contact_form,
                           logged_in=current_user.is_authenticated)


if __name__ == '__main__':
    application.run(debug=True)
