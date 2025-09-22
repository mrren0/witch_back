from datetime import datetime, timedelta

import pytz


class Time:
    timezone = pytz.timezone('Europe/Moscow')

    @classmethod
    def now(cls):
        current_time = datetime.now(cls.timezone)
        return current_time.replace(microsecond=0)

    @classmethod
    def now_plus_hour_for_refresh_token(cls):
        current_time = datetime.now(cls.timezone) + timedelta(hours=6)
        return current_time

    @staticmethod
    def convert_utc_for_msc(utc_time):
        timezone_str = 'Europe/Moscow'
        if isinstance(utc_time, str):
            utc_time = datetime.fromisoformat(utc_time)
        utc_time = utc_time.replace(tzinfo=pytz.UTC)

        local_timezone = pytz.timezone(timezone_str)
        local_time = utc_time.astimezone(local_timezone)

        return local_time.isoformat()
