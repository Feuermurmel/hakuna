import sys


def log(message, *args):
    print(message.format(*args), file=sys.stderr)


def format_date(date):
    return date.strftime('%Y-%m-%d')


def format_time(time):
    return time.strftime('%H:%M')


def format_interval(interval):
    start, end = interval

    return '{} {} - {}'.format(
        format_date(start.date()),
        format_time(start.time()),
        format_time(end.time()))
