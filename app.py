import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)

app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    return "<p>Hello, World!</p>"
