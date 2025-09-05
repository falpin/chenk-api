from .main import *
import uuid

@api.route('/admin/keys', methods=['GET'])
@key_role('developer')
def get_all_keys():
    """Получить все API-ключи (только для разработчиков)"""
    try:
        keys = SQL_request(
            "SELECT key, role, is_active, created_at, updated_at FROM api_keys ORDER BY created_at DESC",
            fetch='all'
        )
        return jsonify({"keys": keys}), 200
    except Exception as e:
        logger.error(f"Ошибка при получении списка ключей: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api.route('/admin/keys', methods=['POST'])
@key_role('developer')
def create_key():
    """Создать новый API-ключ (только для разработчиков)"""
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({"error": "Не указана роль ключа"}), 400
        
        role = data['role']
        # Генерируем уникальный ключ
        api_key = str(uuid.uuid4()).replace('-', '')
        
        # Сохраняем в базу
        SQL_request(
            "INSERT INTO api_keys (key, role) VALUES (?, ?)",
            (api_key, role),
            fetch=None
        )
        
        # Обновляем кеш
        refresh_api_keys()
        
        logger.info(f"Создан новый API-ключ с ролью {role}")
        return jsonify({"key": api_key, "role": role, "message": "Ключ создан"}), 201
        
    except Exception as e:
        logger.error(f"Ошибка при создании ключа: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api.route('/admin/keys/<key>', methods=['PUT'])
@key_role('user')
def update_key(key):
    """Обновить API-ключ (только для разработчиков)"""
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({"error": "Не указана роль ключа"}), 400
        
        role = data['role']
        is_active = data.get('is_active', True)
        
        # Обновляем ключ в базе
        SQL_request(
            "UPDATE api_keys SET role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (role, is_active, key),
            fetch=None
        )
        
        # Обновляем кеш
        refresh_api_keys()
        
        logger.info(f"Обновлен API-ключ {key}: роль={role}, активен={is_active}")
        return jsonify({"message": "Ключ обновлен"}), 200
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении ключа: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api.route('/admin/keys/<key>', methods=['DELETE'])
@key_role('developer')
def delete_key(key):
    """Удалить API-ключ (только для разработчиков)"""
    try:
        # Удаляем ключ из базы
        SQL_request(
            "DELETE FROM api_keys WHERE key = ?",
            (key,),
            fetch=None
        )
        
        # Обновляем кеш
        refresh_api_keys()
        
        logger.info(f"Удален API-ключ {key}")
        return jsonify({"message": "Ключ удален"}), 200
        
    except Exception as e:
        logger.error(f"Ошибка при удалении ключа: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@api.route('/admin/keys/refresh', methods=['POST'])
@key_role('developer')
def refresh_keys():
    """Принудительное обновление кеша ключей (только для разработчиков)"""
    try:
        refresh_api_keys()
        return jsonify({"message": "Кеш API-ключей обновлен"}), 200
    except Exception as e:
        logger.error(f"Ошибка при обновлении кеша: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500