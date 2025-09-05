from flask import Blueprint, jsonify, request, abort, g
from functools import wraps
from middleware import setup_middleware, auth_decorator
import io
from utils import *
from database import SQL_request

api = Blueprint('api', __name__)


@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200
