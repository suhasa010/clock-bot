from collections import defaultdict

from babel import Locale

from clock.domain.finder.zone_finder.find_util import FindUtil
from clock.domain.zone import ZoneFormatter


class LocalizedZoneFinder:
    def __init__(self, zones: iter, locale: Locale):
        self._names_lower = self.__build_names_lower(zones, locale)

    def __build_names_lower(self, zones: iter, locale: Locale):
        names_lower = defaultdict(list)
        for zone in zones:
            for name in self.__get_names_for_zone(zone, locale):
                names_lower[name.lower()].append(zone)
        return names_lower

    @staticmethod
    def __get_names_for_zone(zone, locale):
        return {
            ZoneFormatter.name(zone, locale, zone_variant="generic", short=False),
            ZoneFormatter.name(zone, locale, zone_variant="generic", short=True),
            ZoneFormatter.name(zone, locale, zone_variant="daylight", short=False),
            ZoneFormatter.name(zone, locale, zone_variant="daylight", short=True),
            ZoneFormatter.name(zone, locale, zone_variant="standard", short=False),
            ZoneFormatter.name(zone, locale, zone_variant="standard", short=True),
            ZoneFormatter.location(zone, locale),
        }

    def match_names_lower(self, query_lower):
        return FindUtil.match_key(self._names_lower.items(), query_lower)
