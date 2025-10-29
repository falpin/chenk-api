# main.py
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from vpn_manager import vpn_connection # Импортируем контекстный менеджер

URL = "https://pronew.chenk.ru/blocks/manage_groups/website/"
VPN_CONFIG_PATH = "/data/config.ovpn" # Убедитесь, что путь корректен

def get_courses(complex):
    """
    Получает список курсов и групп для указанного корпуса через VPN.
    """
    with vpn_connection(VPN_CONFIG_PATH) as vpn:
        if vpn is None:
            print("Не удалось подключиться к VPN для получения курсов.")
            return None # Или другое действие при ошибке

        if complex == "Российская":
            complex_param = "list.php?id=3"
        elif complex == "Блюхера":
            complex_param = "list.php?id=1"
        else:
            return None

        try:
            response = requests.get(URL + complex_param)
            response.raise_for_status() # Проверяем статус ответа
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе курсов: {e}")
            return None

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
                    if group_link_tag: # Проверяем, что ссылка существует
                        group_name = group_link_tag.text.strip()
                        group_link = group_link_tag['href'].strip()
                        course_dict[year_name][group_name] = group_link

        return json.dumps(course_dict, ensure_ascii=False, indent=2)

def get_timetable(group):
    """
    Получает расписание для указанной группы через VPN.
    """
    with vpn_connection(VPN_CONFIG_PATH) as vpn:
        if vpn is None:
            print("Не удалось подключиться к VPN для получения расписания.")
            return None # Или другое действие при ошибке

        try:
            response = requests.get(URL + group)
            response.raise_for_status() # Проверяем статус ответа
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе расписания: {e}")
            return None

        schedule_dict = {}
        soup = BeautifulSoup(response.text, 'html.parser')
            
        schedule = soup.find('div', class_='timetableContainer')
        if schedule is None:
            print("Расписание не найдено на странице.")
            return None
            
        days = schedule.find_all('td', attrs={'style': True})

        week = soup.find('span', attrs={'style': 'vertical-align: bottom'})
        text = week.get_text() if week else "Неизвестная неделя"
        week = text.split()[0] if text.split() else "Неизвестная неделя"

        for day in days:
            day_header_div = day.find('div', class_='dayHeader')
            if not day_header_div:
                continue # Пропускаем, если заголовок дня не найден
            day_week = day_header_div.text.strip()

            day_schedule_div = day.find('div', attrs={'style': 'padding-left: 6px;'})
            if not day_schedule_div:
                 print(f"Расписание для дня {day_week} не найдено.")
                 continue # Пропускаем, если расписание дня не найдено

            lessons_list = {}

            lessons = day_schedule_div.find_all('div', class_='lessonBlock')
            i = 0
            for lesson in lessons:
                i += 1
                lesson_time_block_div = lesson.find('div', class_='lessonTimeBlock')
                if not lesson_time_block_div:
                    continue # Пропускаем, если время урока не найдено
                lesson_time_block = lesson_time_block_div.text.strip().split('\n')
                lesson_number = lesson_time_block[0].strip()
                try:
                    lesson_time_start = lesson_time_block[1].strip()
                    lesson_time_finish = lesson_time_block[2].strip()
                except IndexError: # Если не хватает элементов в списке
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
                        continue # Пропускаем отмененные занятия

                    header_div = discBlock.find('div', class_='discHeader')
                    try:
                        span_tag = header_div.find('span')
                        if span_tag:
                            lesson_name_raw = span_tag.get('title', '')
                            lesson_name = re.sub(r'\(.*?\)', '', lesson_name_raw).strip()
                        else:
                            lesson_name = "Без названия" # Или другое значение по умолчанию
                    except AttributeError:
                        lesson_name = "Без названия" # Или другое значение по умолчанию

                    lesson_teachers_data = discBlock.find_all('div', class_='discSubgroup')
                    lesson_data = {}
                    for subgroup in lesson_teachers_data:
                        teacher_div = subgroup.find('div', class_='discSubgroupTeacher')
                        classroom_div = subgroup.find('div', class_='discSubgroupClassroom')
                        
                        teacher = teacher_div.text.strip() if teacher_div else "Неизвестный преподаватель"
                        classroom_raw = classroom_div.text.strip() if classroom_div else "Неизвестная аудитория"
                        classroom = classroom_raw.replace("???", '').strip()

                        lesson_data[teacher] = classroom
                        
                    lesson_info['lessons'] = {lesson_name: lesson_data}

                if lesson_name and lesson_name != "":
                    if lesson_number == "??-??":
                        if i == 1: i = 5
                        lesson_number = str(i) # Убедимся, что это строка
                    lessons_list[lesson_number] = lesson_info
                    try:
                        i = int(lesson_number) # Обновляем i, если номер урока - число
                    except ValueError:
                        pass # Если номер урока не число, оставляем i как есть

            schedule_dict[day_week] = lessons_list

    result = {"week": week, "timetable": schedule_dict}
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(get_courses("Российская"))