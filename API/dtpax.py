from collections import namedtuple
from enum import Enum
from typing import Any
import re

data = dict()
BASE_URL = 'https://api.yarobl.dtpax.ru/api/client/v1'


class Url(str, Enum):
    stations = f'{BASE_URL}/stations'
    routes = f'{BASE_URL}/routes'

    @staticmethod
    def stations_routes(station_id: int) -> str:
        return f'{Url.stations}/{station_id}/routes'


Route_field_names = (
    'route_id', 'name', 'title', 'start_end_stations', 'end_station',
    'vehicle_type_id', 'is_urban', 'num')
Route = namedtuple('Route', Route_field_names)
Station = namedtuple('Station', 'name, address, station_id')
Schedules = namedtuple('schedules', 'name, end_station, arrival_times')


async def get_routes() -> list[Route]:
    async with data['session'].get(f'{BASE_URL}/routes') as resp:
        routes_json: list[dict] = await resp.json()
        routes: list[Route] = list()
        for route_json in routes_json:
            [route_json.pop(key) for key in list(route_json.keys()) if key not in Route_field_names]
            num = int(re.sub(r'\D', '', route_json['name']))
            routes.append(Route(**route_json, is_urban=num < 100, num=num))
        return routes


########################################################################################################################

from dateutil.parser import parse
from datetime import datetime, timedelta


async def get_station_by_name(name: str) -> list[Station]:
    async with data['session'].get(Url.stations + f'?station_name={name}') as resp:
        json_stations: list[dict[str, Any]] = await resp.json()
        stations = list()
        for json_station in json_stations:
            station = Station(
                name=json_station['name'],
                address=json_station['address'],
                station_id=json_station['station_id']
            )
            stations.append(station)
        return stations


def tz(s: str):
    if s.endswith('Z'):
        return s.replace('Z', '+00:00')
    return s


def post_parse(d: datetime):
    if d.tzname() == 'UTC':
        return d + timedelta(hours=3)
    return d


async def get_station_by_id(sid):
    url = f'https://api.yarobl.dtpax.ru/api/client/v1/stations/{sid}'
    async with data['session'].get(url) as resp:
        json_stations: dict = await resp.json()
        return json_stations.get('name')


async def get_time_by_st_id(st_id) -> list[Station]:
    url = f'https://api.yarobl.dtpax.ru/api/client/v1/stations/{st_id}/schedules/nearest?nearest_vehicle_amount=3'
    async with data['session'].get(url) as resp:
        json_stations: list = await resp.json()
        schedules = list()
        for json_station in json_stations:
            schedule = Schedules(
                name=json_station['route']['name'],
                end_station=json_station['route']['end_station'],
                arrival_times=[post_parse(parse(tz(t['arrival_time']))) for t in json_station['vehicle_arrival_time']]
            )
            schedules.append(schedule)
        return schedules
