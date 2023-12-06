from bot.handlers.hub import router as router_hub
from bot.handlers.schedule import router as router_schedule
from bot.handlers.stations import router as router_stations
from bot.handlers.unknown import router as router_unknown

routers = (
    router_hub,
    router_schedule,
    router_stations,
    router_unknown
)
