import json
from collections import namedtuple

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = 'https://yargortrans.ru'
Route = namedtuple('Route', 'rid, num, vt, name, start, finish, link, feature')
Schedule = namedtuple('Schedule', 'url, rid, title, num, itinerary, note, station_start, station_end, is_reverse, info_head, info, stations, is_schedule, schedule')


def as_route(element: Tag, vt: int) -> Route:
    """
    Преобразует элемент <li><a>{num}. {start} - {finish} (<i>{feature}</i>)</a></li> в объект типа Route
    :param vt:
    :param element: PageElement из BeautifulSoup
    :return: namedtuple('Route', 'num, name, start, finish, link, feature')
    """
    name = (element.text
            if not element.i else
            element.replace_with(element.i, '').text.strip('()')
            ).replace('\n', ' ').replace('  ', ' ').strip().split('.\xa0', 1)
    stations = name[-1].split(' - ', 1)
    return Route(
        rid=int(element.a['href'].split('=')[-1]),
        num=name[0] if len(name) > 1 else None,
        vt=vt,
        name=name[-1],
        start=stations[0],
        finish=stations[1],
        link=element.a['href'],
        feature=element.i.text if element.i else None
    )


def website_get_all_routes(link: str = f'{BASE_URL}/list.php?vt=', vt: int = 1) -> list[Route]:
    """
    Парсит список маршрутов с <a href="https://yargortrans.ru">YarGorTrans.ru</a>
    :param link: Ссылка на сайт
    :param vt: Тип маршрута (от 1 до 5):
               1 - Автобусные маршруты
               2 - Троллейбусные маршруты
               3 - Трамвайные маршруты
               4 - Маршрутные такси
               5 - Бесплатные автобусы ТЦ «Глобус»
    :return: Список объектов Route
    """
    page = requests.get(f'{link}{vt}').text
    soup = BeautifulSoup(page, 'html.parser')
    route_list = soup.findAll('li', class_='route_list_item')
    return [as_route(item, vt=vt) for item in route_list]


def website_get_route(rid: str | int = 463, *, base_url: str = f'{BASE_URL}/config.php?rid=') -> Schedule:
    """
    Парсит маршрут с сайта <a href="https://yargortrans.ru">YarGorTrans.ru</a>
    <pre>
    url: str(url) – Ссылка на маршрут;
    rid: int – Ид маршрута;
    title: str – Заголовок маршрута (номер и остановки);
    num: str – Номер маршрута;
    itinerary: str – начальная и конечная остановка;
    note: str | None – заметка к некоторым маршрутам;
    station_start: str – остановка, с которой начинается маршрут;
    station_end: str – конечная остановка;
    is_reverse: bool – есть ли обратное направление;
    info_head: list[str * 4] – русские названия информации;
    info: dict – информация о маршруте:
    .... "Прямое"/?"Обратное"?:
    .... .... stations_count: int – кол-во остановок;
    .... .... distance: float – расстояние в километрах;
    .... .... time: int – время прохождения маршрута;
    stations: list – список остановок:
    .... "Перечень остановок в прямом/?обратном? направлении"
    .... .... name: str – Название;
    .... .... link: str(url) – Ссылка YarGorTrans.ru;
    is_schedule: bool – Есть ли расписание у маршрута;
    schedule: dict | None – Расписание маршрута
    .... ?"Рабочие дни"?/?"Выходные дни"?/?"Ежедневно"?/?*Другое*?
    .... .... *начальная*: str
    .... .... *конечная*: str
    </pre>
    :param rid: Ид маршрута (с сайта YarGorTrans.ru), иначе ссылка?
    :param base_url: Шаблон ссылки [НЕ ИСПОЛЬЗОВАТЬ!]
    :return: Словарь с информацией о маршруте
    """
    if isinstance(rid, str) and rid.startswith(f'{BASE_URL}/config.php?rid='):
        url = rid
        rid = rid.split('?rid=')[-1]
    else:
        url = f'{base_url}{rid}'
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    title, h2, h3, tables = soup.find('h1').text, soup.find('h2'), soup.findAll('h3'), soup.findAll('table')

    itinerary = h2.text
    note = h2.find('i')
    if note:
        itinerary = itinerary.replace(note.text, '')
        note = note.text
    station_start, station_end = itinerary.split(' - ')

    # Наличие перечня остановок и расписания в обратном направлении
    is_reverse = any(['обрат' in item.text for item in h3])

    # Информация о количестве остановок, расстоянии и времени прохождения
    info_head = [item.text for item in tables[0].findAll('th')]
    raw_info = [item.text for item in tables[0].findAll('td')]
    info = {raw_info[i * 4]: dict(
        stations_count=int(raw_info[i * 4 + 1]), distance=float(raw_info[i * 4 + 2]), time=int(raw_info[i * 4 + 3])
    ) for i in range(len(raw_info) // 4)}

    # Список остановок
    st_directs = [item.text for item in h3 if 'Перечень' in item.text]
    st_data = [
        [dict(name=station.text, url=f'{BASE_URL}/{station.get("href")}')
         for station in direct.findAll('a')]
        for direct in soup.findAll('div', class_='stations_list')]
    stations = {st_directs[i]: st_data[i] for i in range(len(st_directs))}

    # Расписание
    is_schedule = any(['расписание' in item.text.lower() for item in h3])
    schedule = None
    if is_schedule:
        stops = [tag.text for tag in tables[-1].findAll('b')]
        sch = [tag.text for tag in tables[-1].findAll('td')]
        if sum(map(len, stops)) == 0:
            stops = [station_start, station_end]
        schedule = dict(zip(sch[::3], [dict(zip(stops, sch[i * 3 + 1: i * 3 + 3])) for i in range(len(sch) // 3)]))

    return Schedule(
        url=url, rid=int(rid), title=title, num=title.split(' ')[-1], itinerary=itinerary, note=note,
        station_start=station_start, station_end=station_end, is_reverse=is_reverse, info_head=info_head, info=info,
        stations=stations, is_schedule=is_schedule, schedule=schedule
    )


def __print_list_route(list_or_routes: list[Route]) -> None:
    """
    Для отладки.
    Выводит в консоль список маршрутов в красивом виде
    :param list_or_routes: Список объектов Route
    """
    out = [
        str('{:4} {:70} {:40} {:47} {:19} {}'.format(*map(str, route))
            ).replace("'", '').strip('[]')
        for route in list_or_routes
    ]
    print(*out, sep='\n', end='\n' * 5)

# for i in range(6):
#     __print_list_route(get_routes(vt=i + 1))

# print(json.dumps(get_route(463), indent=2, ensure_ascii=False))
# print('\n\n----------------------------------------------------------------------------\n')
# print(json.dumps(get_route(780), indent=2, ensure_ascii=False))
# print('\n\n----------------------------------------------------------------------------\n')
# print(json.dumps(get_route(104), indent=2, ensure_ascii=False))
