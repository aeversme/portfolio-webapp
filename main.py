from flask import Flask, render_template

from dotenv import load_dotenv
from datetime import date
import os

app = Flask(__name__)

load_dotenv()
current_year = date.today().year

app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')


@app.route('/')
def get_index():
    return render_template('index.html', year=current_year)


@app.route('/about')
def get_about_page():
    return render_template('about.html', year=current_year)


@app.route('/projects')
def get_projects():
    return render_template('/projects.html', year=current_year)


@app.route('/blog')
def get_all_posts():
    return render_template('blog.html', year=current_year)


@app.route('/resume')
def get_resume():
    return render_template('resume.html', year=current_year)


@app.route('/contact', methods=['GET', 'POST'])
def contact_me():
    return render_template('contact.html', year=current_year)


if __name__ == '__main__':
    app.run(debug=True)
