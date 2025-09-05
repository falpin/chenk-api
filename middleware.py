from functools import wraps
import os
import time
from flask import request, jsonify, g, current_app
from database import SQL_request
import logger
from dotenv import load_dotenv

load_dotenv()
logger = logger.setup(os.getenv("DEBUG"), name="middleware", log_path=os.getenv("LOG_PATH"))

_api_keys_cache = {}
_cache_last_updated = 0
CACHE_TTL = 300

def _refresh_api_keys_cache():  #Обновляет кеш API-ключей из базы данных
    global _api_keys_cache, _cache_last_updated
    
    try:
        result = SQL_request(
            "SELECT key, role FROM api_keys WHERE is_active = 1",
            fetch='all'
        )
        
        if result:
            _api_keys_cache = {item['key']: item['role'] for item in result}
            _cache_last_updated = time.time()
            logger.info(f"Обновлен кеш API-ключей. Загружено ключей: {len(_api_keys_cache)}")
        else:
            logger.warning("Не найдено активных API-ключей в базе данных")
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке API-ключей из базы: {e}")

def _get_api_key_role(api_key):  #Получает роль API-ключа (с использованием кеша)
    global _cache_last_updated
    
    if not _api_keys_cache or time.time() - _cache_last_updated > CACHE_TTL:
        _refresh_api_keys_cache()
    
    if api_key in _api_keys_cache:
        return _api_keys_cache[api_key]
    
    
    try: # Если ключа нет в кеше, проверяем напрямую в базе
        result = SQL_request(
            "SELECT role FROM api_keys WHERE key = ? AND is_active = 1",
            (api_key,),
            fetch='one'
        )
        
        if result:
            role = result['role']
            _api_keys_cache[api_key] = role
            return role
    
    except Exception as e:
        logger.error(f"Ошибка при проверке API-ключа в базе: {e}")
    
    return None

def key_role(required_role=None):  #Декоратор для проверки API-ключа и его роли
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                return jsonify({"error": "API ключ отсутствует"}), 401
            
            actual_role = _get_api_key_role(api_key)
            
            if not actual_role:
                return jsonify({"error": "Неверный API ключ"}), 403
            
            if required_role and actual_role != required_role:
                return jsonify({"error": "Недостаточно прав"}), 403
            
            g.api_key = api_key
            g.api_key_role = actual_role
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_middleware(app):
    _refresh_api_keys_cache()
    
    @app.before_request
    def logging_middleware():
        logger.debug(f"Запрос: {request.method} {request.path}")