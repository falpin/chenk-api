from flask import Blueprint, jsonify, request, abort, g
from functools import wraps
from middleware import setup_middleware, key_role
import io
from utils import *
from database import SQL_request

api = Blueprint('api', __name__)

@api.route('/', methods=['GET'])
@key_role()
def example():
    return jsonify({"message": "API Работает"}), 200
