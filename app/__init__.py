from flask import Flask

app = Flask(__name__)
app.secret_key = 'random string'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

from app import routes