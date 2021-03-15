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


if __name__ == '__main__':
    app.run(debug=True)
