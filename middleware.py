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

# Добавляем кеш для иерархии ролей
_roles_hierarchy_cache = None

def refresh_api_keys():
    _refresh_api_keys_cache()
    return True

def _refresh_api_keys_cache():
    global _api_keys_cache, _cache_last_updated, _roles_hierarchy_cache
    
    try:
        # Загружаем ключи и роли
        result = SQL_request(
            "SELECT ak.key, ak.role, r.priority FROM api_keys ak "
            "JOIN roles r ON ak.role = r.name WHERE ak.is_active = 1",
            fetch='all'
        )
        
        if result:
            _api_keys_cache = {item['key']: {'role': item['role'], 'priority': item['priority']} for item in result}
            _cache_last_updated = time.time()
            logger.info(f"Обновлен кеш API-ключей. Загружено ключей: {len(_api_keys_cache)}")
        else:
            logger.warning("Не найдено активных API-ключей в базе данных")
            
        # Загружаем иерархию ролей
        roles_result = SQL_request(
            "SELECT name, priority FROM roles ORDER BY priority DESC",
            fetch='all'
        )
        if roles_result:
            _roles_hierarchy_cache = {role['name']: role['priority'] for role in roles_result}
            logger.info(f"Обновлена иерархия ролей: {_roles_hierarchy_cache}")
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из базы: {e}")

def _get_api_key_info(api_key):
    global _cache_last_updated
    
    if not _api_keys_cache or time.time() - _cache_last_updated > CACHE_TTL:
        _refresh_api_keys_cache()
    
    if api_key in _api_keys_cache:
        return _api_keys_cache[api_key]
    
    try:
        result = SQL_request(
            "SELECT ak.role, r.priority FROM api_keys ak "
            "JOIN roles r ON ak.role = r.name "
            "WHERE ak.key = ? AND ak.is_active = 1",
            (api_key,),
            fetch='one'
        )
        
        if result:
            role_info = {'role': result['role'], 'priority': result['priority']}
            _api_keys_cache[api_key] = role_info
            return role_info
    
    except Exception as e:
        logger.error(f"Ошибка при проверке API-ключа в базе: {e}")
    
    return None

def _check_role_access(user_priority, required_priority, check_mode):
    """Проверяет доступ в зависимости от режима проверки"""
    if check_mode == 'exact':
        return user_priority == required_priority
    elif check_mode == 'min':
        return user_priority >= required_priority
    return False

def key_role(required_role=None, check_mode='min'):
    """
    Декоратор для проверки ролей с поддержкой иерархии
    
    :param required_role: Требуемая роль (строка или список строк)
    :param check_mode: Режим проверки:
        - 'min': минимальная требуемая роль (по умолчанию)
        - 'exact': точное совпадение роли
        - 'any': любая из перечисленных ролей
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                return jsonify({"error": "API ключ отсутствует"}), 401
            key_info = _get_api_key_info(api_key)
            
            if not key_info:
                return jsonify({"error": "Неверный API ключ"}), 403
            
            user_role = key_info['role']
            user_priority = key_info['priority']
            
            if required_role is not None:
                if isinstance(required_role, list):
                    if check_mode == 'any':
                        if user_role not in required_role:
                            return jsonify({"error": "Недостаточно прав"}), 403
                    else:
                        required_priority = min([
                            _roles_hierarchy_cache[role] 
                            for role in required_role 
                            if role in _roles_hierarchy_cache
                        ])
                        if not _check_role_access(user_priority, required_priority, check_mode):
                            return jsonify({"error": "Недостаточно прав"}), 403
                else:
                    # Одиночная роль
                    required_priority = _roles_hierarchy_cache.get(required_role)
                    if required_priority is None or not _check_role_access(user_priority, required_priority, check_mode):
                        return jsonify({"error": "Недостаточно прав"}), 403
            
            g.api_key = api_key
            g.api_key_role = user_role
            g.api_key_priority = user_priority
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_middleware(app):
    app.config['ROLES_HIERARCHY'] = _roles_hierarchy_cache