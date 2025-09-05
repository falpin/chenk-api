from flask import Blueprint, jsonify, request, abort, g
from functools import wraps
from middleware import setup_middleware, key_role, refresh_api_keys
import io
from utils import *
from database import SQL_request
import logger

logger = logger.setup()

api = Blueprint('api', __name__)

@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200
