from .main import *

@api.route('/groups', methods=['GET'])
def groups():
    return jsonify({"message": "Все группы"}), 200