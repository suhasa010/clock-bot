from babel import Locale, UnknownLocaleError
from bot.action.core.action import Action
from bot.multithreading.work import Work

from clock.bot.inline.query.result.generator import ResultGenerator
from clock.domain.time import TimePoint
from clock.finder.api import ZoneFinderApi
from clock.log.api import LogApi
from clock.storage.api import StorageApi


MAX_RESULTS_PER_QUERY = 50

DEFAULT_LOCALE = Locale.parse("en_US")


class InlineQueryClockAction(Action):
    def __init__(self):
        super().__init__()
        self.zone_finder_api = None  # initialized in post_setup when we have access to config

    def post_setup(self):
        self.zone_finder_api = ZoneFinderApi(bool(self.config.enable_countries))

    def process(self, event):
        current_time = TimePoint.current()

        query = event.query
        locale = self.__get_locale(query)

        zones = self.zone_finder_api.find(query.query, locale, current_time)

        offset = self.__get_offset(query)
        offset_end = offset + MAX_RESULTS_PER_QUERY
        next_offset = self.__get_next_offset(len(zones), offset_end)

        results = ResultGenerator.generate(current_time, locale, zones[offset:offset_end])

        processing_time = TimePoint.current_timestamp() - current_time.timestamp

        self.api.async.answerInlineQuery(
            inline_query_id=query.id,
            results=results,
            next_offset=next_offset,
            cache_time=0,
            is_personal=True
        )

        self.scheduler.io(Work(
            lambda: StorageApi.get().save_query(query, current_time, locale, zones, results, processing_time),
            "storage:save_query"
        ))

        # event.logger is async
        LogApi.get(event.logger).log_query(query, current_time, locale, zones, results, processing_time)

    @staticmethod
    def __get_locale(query):
        user_locale_code = query.from_.language_code
        try:
            locale = Locale.parse(user_locale_code, sep="-")
        except UnknownLocaleError:
            locale = None
        if locale is None:
            locale = DEFAULT_LOCALE
        return locale

    @staticmethod
    def __get_offset(query):
        offset = query.offset
        if offset and offset.isdigit():
            return int(offset)
        return 0

    @staticmethod
    def __get_next_offset(result_number, offset_end):
        if result_number > offset_end:
            return str(offset_end)
        return None
