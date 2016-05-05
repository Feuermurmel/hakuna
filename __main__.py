import datetime
import json

from lib.hakuna import HakunaSession
from lib.sleepwake import intervals_by_date


def intervals_overlap(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2

    return start1 < end2 and start2 < end1


def load_config():
    with open('config.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def main():
    config = load_config()

    session = HakunaSession(
        base_uri=config['base_uri'],
        username=config['username'],
        password=config['password'])

    today = datetime.date.today()

    for date, intervals in intervals_by_date():
        if date < today:
            existing_intervals = session.get_entries(date)

            for interval in intervals:
                if not any(intervals_overlap(i, interval) for i in existing_intervals):
                    session.enter_time(interval)


main()
