from os import getenv, path

from dotenv import load_dotenv
from flask import Flask

from database import db

load_dotenv()

app = Flask(__name__)

app.debug = getenv('DEBUG', 'False').lower() == 'true'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % path.join(path.dirname(__file__), 'db.sqlite')

db.init_app(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return "<p>Hello, World!</p>"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
