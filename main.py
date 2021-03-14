from flask import Flask, render_template
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')


@app.route('/')
def get_index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
