from flask import Flask
from dotenv import load_dotenv
from extensions import cors
from routes import *
import os
import logger

from utils import *
from config import *


load_dotenv()
logger = logger.setup()

for var in config.required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Переменная окружения {var} не задана в .env")

def create_app():
    app = Flask(__name__)
    
    cors.init_app(app)

    app.register_blueprint(api)

    app.config["SECRET_KEY"] = SECRET_KEY
    setup_middleware(app)

    return app

app = create_app()

if __name__ == '__main__':
    logger.info("Сервер запущен")
    app.run(port=5000, debug=config.DEBUG, host='0.0.0.0')