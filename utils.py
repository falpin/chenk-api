import json
from datetime import datetime
import pytz
import os
import re
from database import *


def now_time():  # Получение текущего времени по МСК
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M:%S")
    current_date = now_moscow.strftime("%Y.%m.%d")
    return current_date, current_time

def save_groups(data):
    for course, groups in data.items():
        if course == 'complex':
            continue
        for group_name, url in groups.items():
            date, time = now_time()  # Обновляем время для каждой группы
            timestamp = f"{date} {time}"
            SQL_request("""
                INSERT INTO groups (complex, group_name, url, course, time_add)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(group_name) DO UPDATE SET
                    complex = excluded.complex,
                    url = excluded.url,
                    course = excluded.course,
                    time_add = excluded.time_add  -- Обновляем время добавления
            """, (data['complex'], group_name, url, course, timestamp))

def save_schedule(get_data):
    week = get_data["week"]
    new_data = get_data.copy()
    del new_data["week"]
    get_data = new_data
    for group in get_data:
        data = get_data[group]
        group = group.replace("-", "_")
        create_group(group)
        date, time = now_time()  # Обновляем время для каждой группы
        timestamp = f"{date} {time}"
        SQL_request(f"""
            INSERT INTO {group} (week, data, time_add)
            VALUES (?, ?, ?)
            ON CONFLICT(week) DO UPDATE SET
                data = excluded.data,
                time_add = excluded.time_add
        """, (week, json.dumps(data), timestamp))


def find_groups(find_group=None):
    groups = SQL_request("SELECT * FROM groups", all_data=True)
    if groups:
        groups_list = {}
        for group in groups:
            group_dict = {
                "id": group[0],
                "complex": group[1],
                "url": group[3],
                "course": group[4]
            }
            groups_list[group[2]] = (group_dict)
        try:
            if find_group:
                groups_list = groups_list[find_group]
        except:
            return "Группа не найдена", 400
        groups_json = json.dumps(groups_list, indent=4, ensure_ascii=False)
        return groups_list, 200
    else:
        return None, 400

def find_schedule(group, week=None):
    group = group.replace("-", "_")
    if week is None:
        week = now_week()
    try:
        data = SQL_request(f"SELECT * FROM '{group}' WHERE week={week}", all_data=True)
        schedule = {}
        schedule["week"] = data[0][0]
        schedule["schedule"] = json.loads(data[0][1])
    except Exception as e:
        return "Расписание не найдено", 400
    return schedule, 200