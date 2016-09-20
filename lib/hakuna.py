from datetime import date, datetime
from urllib.parse import urljoin

from pytz import timezone
from requests import session
from bs4 import BeautifulSoup

from .util import log, format_date, format_interval


class HakunaSession:
    _timezone = timezone('Europe/Zurich')

    def __init__(self, base_uri, username, password):
        self._session = session()

        response = self._session.get(base_uri)

        assert response.status_code == 200

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        query = {
            element['name']: element.get('value', None)
            for element
            in form.find_all('input')}

        query.update(username=username, password=password)

        response = self._session.post(
            urljoin(response.url, form['action']), query)

        assert response.status_code == 200

        soup = BeautifulSoup(response.text, 'html.parser')

        self._csrf_token = soup.find('meta', dict(name='csrf-token'))['content']
        self._time_entries_url = response.url

    def get_entries(self, date: date):
        log('Getting entries on {} ...', format_date(date))

        url = '{}/date/{}'.format(
            self._time_entries_url,
            date.strftime('%Y-%m-%d'))

        response = self._session.get(url)

        assert response.status_code == 200

        soup = BeautifulSoup(response.text, 'html.parser')

        def iter_intervals():
            for i in soup.find_all(class_='timestamps'):
                def get_time(class_):
                    text = i.find(class_=class_)
                    time = datetime.strptime(text.text.strip(), '%H:%M').time()

                    return self._timezone.localize(datetime.combine(date, time))

                yield get_time('start-time'), get_time('end-time')

        return list(iter_intervals())

    def enter_time(self, interval):
        log('Adding entry {} ...', format_interval(interval))

        start, end = interval
        start = start.astimezone(self._timezone)
        end = end.astimezone(self._timezone)

        date = start.date()

        assert end.date() == date

        response = self._session.post(
            self._time_entries_url,
            headers={'X-CSRF-Token': self._csrf_token},
            data={
                'utf8': '✓',
                'time_entry[start_time]': start.strftime('%H:%M'),
                'time_entry[end_time]': end.strftime('%H:%M'),
                'time_entry[time_type_id]': '1',
                'time_entry[project_id]': '',
                'time_entry[start_date]': date.strftime('%Y-%m-%d'),
                'time_entry[note]': '',
                'commit': 'Speichern'})

        assert response.status_code == 200
