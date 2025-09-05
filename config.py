import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DB_PATH = os.getenv("DB_PATH")
JWT_ACCESS_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_EXPIRES_HOURS", "24"))
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]
required_env_vars = ["SECRET_KEY", "DB_PATH"]