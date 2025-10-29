from FlaskAPIServer import *
import FlaskAPIServer as fas
from datetime import datetime

from database import SQL_request as SQL, create_group, delete_group
import parser 


COMPLEX = ["Блюхера", "Российская"]


@api.route('/', methods=['GET'])
def test():
    return jsonify({"success": True}), 200


@api.route('/update/groups', methods=['GET'])
@key_role("admin")
def update_groups():
    updated_groups = set()  # Для отслеживания обновлённых групп

    for complex_name in COMPLEX:
        groups = json.loads(parser.get_courses(complex_name))
        if groups == {}:
            return jsonify({"success": False, "error":"Не удалось получить список групп"}), 500
        
        for course_name, group_data in groups.items():
            course_number = int(course_name.split()[0])
            for group_name, link in group_data.items():
                group_name = group_name.replace("-","_")

                existing_group = SQL("""
                    SELECT id FROM groups WHERE group_name = ? AND complex_name = ? AND course = ?
                """, (group_name, complex_name, course_number), "one")

                if existing_group: # Обновляем существующую группу
                    SQL(""" UPDATE groups SET link = ?, time_update = ? WHERE id = ? """, (link, datetime.now(), existing_group["id"]), "one")
                else: # Добавляем новую группу
                    create_group(group_name) # Создаем таблицу этой группы для расписания
                    SQL("""
                        INSERT INTO groups (group_name, complex_name, link, course)
                        VALUES (?, ?, ?, ?)
                    """, (group_name, complex_name, link, course_number), "one")

                updated_groups.add((group_name, complex_name, course_number))

    all_groups = SQL(""" SELECT id, group_name, complex_name, course FROM groups """, (), "all")

    updated_group_names = {item[0] for item in updated_groups} 
    for group in all_groups:
        group_id = group["id"]
        group_name = group["group_name"]
        if group_name not in updated_group_names:
            delete_group(group_name) # Удаление таблицы, если группа больше не активна
            SQL("""
                UPDATE groups
                SET status = 'inactive', time_update = ?
                WHERE id = ?
            """, (datetime.now(), group_id), "one")

    return jsonify({"success": True, "message":"Группы обновлены"}), 201


@api.route('/update/timetable', methods=['GET'])
@key_role("admin")
def all_update_timetable():
    for complex_name in COMPLEX:
        groups = json.loads(parser.get_courses(complex_name))
        for course_name, group_data in groups.items():
            for group_name, link in group_data.items():
                update_timetable(complex_name, group_name)
    return jsonify({"success": True, "message":"Расписание для всех групп обновлено"}), 201


@api.route('/<complex_name>/<group_name>/update', methods=['GET'])
@key_role("admin")
def update_timetable(complex_name, group_name):
    group_name = group_name.replace("-","_")
    group = SQL("SELECT * FROM groups WHERE complex_name = ? AND group_name = ?", (complex_name, group_name), "one")

    if group:
        link = group["link"]
    else:
        group_name = group_name.replace("_","-")
        return jsonify({"success": False, "error":f"Группа {group_name} не надена в базе данных"}), 404

    data = parser.get_timetable(link)
    if data:
        data = json.loads(data)
    else:
        return jsonify({"success":False, "error":"Не удалось получить данные"}), 500

    current_week = SQL(f"SELECT * FROM {group_name} WHERE week_id = ?", (data["week"],), "one")
    if current_week:
        SQL(f"UPDATE {group_name} SET timetable = ?, time_update = ? WHERE week_id = ? """, (json.dumps(data["timetable"], ensure_ascii=False), datetime.now(), current_week["week_id"]), "one")
    else:
        SQL(f"INSERT INTO {group_name} (week_id, timetable) VALUES (?, ?) """, (data["week"], json.dumps(data["timetable"], ensure_ascii=False)), "one")

    group_name = group_name.replace("_","-")
    return jsonify({"success": True, "message":f"Расписание для группы {group_name} обновлено"}), 201


@api.route('/<complex_name>', methods=['GET'])
def get_groups(complex_name):
    groups = SQL("SELECT * FROM groups WHERE complex_name = ?", (complex_name,), "all")
    return jsonify({"success":True, "data":groups}), 200


@api.route('/<complex_name>/<group_name>', methods=['GET'])
def get_timetable(complex_name ,group_name): # Получение расписания
    group_name = group_name.replace("-","_")
    group = SQL("SELECT * FROM groups WHERE complex_name = ? AND group_name = ?", (complex_name, group_name), "one")
    if group:
        timetable = SQL(f"SELECT * FROM {group_name} ORDER BY created_at DESC LIMIT 1;", (), "one")
        return jsonify({"success": True, "data":{"week": timetable["week_id"], "timetable":timetable["timetable"] }}), 200
    group_name = group_name.replace("_","-")
    return jsonify({"success": False, "error":f"Группа {group_name} не надена в базе данных"}), 404


if __name__  == "__main__":
    fas.start_server()
else:
    app = fas.create_app()