import logging
import datetime

from flask import Flask, jsonify
from flask_cors import CORS

from database import db
from config import settings
from services.errors import ServiceError
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)


@app.errorhandler(ServiceError)
def handle_service_error(error):
    return jsonify({'error': error.message}), error.status_code

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
