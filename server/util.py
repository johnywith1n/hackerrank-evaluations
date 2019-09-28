import pytz
from datetime import datetime


def convert_timestamp_to_pacific_datetime(ts):
    date = datetime.utcfromtimestamp(ts)
    utc_tz = pytz.timezone('utc')
    date = utc_tz.localize(date)
    pacific_date = date.astimezone(pytz.timezone('US/Pacific'))
    fmt = '%b %d %Y'
    return pacific_date.strftime(fmt)
