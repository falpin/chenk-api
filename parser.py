import requests
from bs4 import BeautifulSoup
import re
import json
import subprocess
import time
import signal
import os
from contextlib import contextmanager

URL = "https://pronew.chenk.ru/blocks/manage_groups/website/"

class VPNManager:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.process = None
    
    def connect(self):
        """Подключиться к VPN"""
        try:
            # Запускаем OpenVPN в фоновом режиме
            self.process = subprocess.Popen([
                'openvpn', 
                '--config', 
                self.config_file_path,
                '--daemon'  # запуск в фоне
            ])
            
            # Ждем некоторое время для установления соединения
            time.sleep(5)
            print("VPN подключен")
            return True
        except Exception as e:
            print(f"Ошибка подключения к VPN: {e}")
            return False
    
    def disconnect(self):
        """Отключиться от VPN"""
        if self.process:
            try:
                # Убиваем процесс OpenVPN
                self.process.terminate()
                self.process.wait(timeout=5)
                print("VPN отключен")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("VPN процесс принудительно завершен")
            except Exception as e:
                print(f"Ошибка отключения VPN: {e}")

@contextmanager
def vpn_connection(config_file_path):
    """Контекстный менеджер для VPN соединения"""
    vpn = VPNManager(config_file_path)
    try:
        if vpn.connect():
            yield vpn
        else:
            raise Exception("Не удалось подключиться к VPN")
    finally:
        vpn.disconnect()

# Используем вашу конфигурацию OpenVPN
VPN_CONFIG_PATH = "config.ovpn"  # Укажите путь к вашему файлу

def get_courses(complex):
    with vpn_connection(VPN_CONFIG_PATH):
        if complex == "Российская":
            complex = "list.php?id=3"
        elif complex == "Блюхера":
            complex = "list.php?id=1"
        else:
            return None

        response = requests.get(URL + complex)
        soup = BeautifulSoup(response.text, 'html.parser')
        courses = soup.find_all('div', class_='spec-year-block-container')
        course_dict = {}

        for course in courses:
            spec_course_blocks = course.find_all('div', class_='spec-year-block')
            for spec_course in spec_course_blocks:
                year_name = spec_course.find(
                    'span', class_='spec-year-name').text.strip()
                year_name = year_name.replace(":", '')

                if year_name not in course_dict:
                    course_dict[year_name] = {}

                groups = spec_course.find_all('span', class_='group-block')
                for group in groups:
                    group_link_tag = group.find('a')
                    group_name = group_link_tag.text.strip()
                    group_link = group_link_tag['href'].strip()
                    course_dict[year_name][group_name] = group_link

        return json.dumps(course_dict, ensure_ascii=False)

def get_timetable(group):
    with vpn_connection(VPN_CONFIG_PATH):
        response = requests.get(URL + group)
        schedule_dict = {}

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
                
            schedule = soup.find('div', class_='timetableContainer')
            if schedule is None:
                return None
                
            days = schedule.find_all('td', attrs={'style': True})

            week = soup.find('span', attrs={'style': 'vertical-align: bottom'})
            text = week.get_text()
            week = text.split()[0]

            for day in days:
                day_week = day.find('div', class_='dayHeader').text.strip()
                day_schedule = day.find(
                    'div', attrs={'style': 'padding-left: 6px;'})

                lessons_list = {}

                lessons = day_schedule.find_all(
                    'div', class_='lessonBlock')
                i = 0
                for lesson in lessons:
                    i += 1
                    lesson_time_block = lesson.find(
                        'div', class_='lessonTimeBlock').text.strip().split('\n')
                    lesson_number = lesson_time_block[0].strip()
                    try:
                        lesson_time_start = lesson_time_block[1].strip()
                        lesson_time_finish = lesson_time_block[2].strip()
                    except:
                        lesson_time_start = "???"
                        lesson_time_finish = "???"

                    lesson_info = {
                        "time_start": lesson_time_start,
                        "time_finish": lesson_time_finish,
                        "lessons": {}
                    }

                    lesson_name = None
                    discBlocks = lesson.find_all('div', class_='discBlock')
                    for discBlock in discBlocks:
                        if 'cancelled' in discBlock.get('class', []):
                            continue

                        header_div = discBlock.find('div', class_='discHeader')
                        try:
                            lesson_name = header_div.find('span').get('title')
                            lesson_name = re.sub(r'\(.*?\)', '', lesson_name)
                            lesson_name = lesson_name.strip()
                        except:
                            lesson_name = None

                        lesson_teachers_data = discBlock.find_all('div', class_='discSubgroup')
                        lesson_data = {}
                        for subgroup in lesson_teachers_data:
                            teacher = subgroup.find(
                                'div', class_='discSubgroupTeacher').text.strip()
                            classroom = subgroup.find('div', class_='discSubgroupClassroom').text.strip()
                            classroom = classroom.replace("???", '')
                            lesson_data[teacher] = classroom
                            
                        lesson_info['lessons'] = {lesson_name: lesson_data}

                    if lesson_name is not None and lesson_name != "":
                        if lesson_number == "??-??":
                            if i == 1: i = 5
                            lesson_number = i
                        lessons_list[lesson_number] = lesson_info
                        i = int(lesson_number)

                schedule_dict[day_week] = lessons_list

        else:
            schedule_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

        return json.dumps({"week": week, "timetable": schedule_dict}, ensure_ascii=False)

# Альтернативный вариант - сессия с VPN для нескольких запросов
def create_vpn_session(config_path):
    """Создает VPN соединение и возвращает сессию для нескольких запросов"""
    vpn = VPNManager(config_path)
    if vpn.connect():
        return vpn, requests.Session()
    else:
        raise Exception("Не удалось подключиться к VPN")

def close_vpn_session(vpn, session):
    """Закрывает VPN соединение и сессию"""
    vpn.disconnect()
    session.close()

if __name__ == "__main__":
    # Пример использования
    print(get_courses("Российская"))
    # print(get_timetable("view.php?gr=343&dep=3"))