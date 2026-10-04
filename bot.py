"""Cycling forecast preview and explicit Telegram delivery."""
import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/Amsterdam')


def load_env():
    path = Path('.env')
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def forecast():
    key = os.getenv('OPENWEATHER_API_KEY')
    if not key:
        raise RuntimeError('Set OPENWEATHER_API_KEY in .env, or run --demo.')
    query = urlencode({'lat': os.getenv('LATITUDE', '52.3676'),
                       'lon': os.getenv('LONGITUDE', '4.9041'),
                       'appid': key, 'units': 'metric'})
    try:
        with urlopen('https://api.openweathermap.org/data/2.5/forecast?' + query,
                     timeout=20) as response:
            return json.load(response)['list']
    except HTTPError as error:
        raise RuntimeError(f'OpenWeather returned HTTP {error.code}; check API access.') from None
    except (URLError, TimeoutError, ValueError, KeyError):
        raise RuntimeError('Forecast unavailable or invalid; try again later.') from None


def recommend(entries, day, start_hour, end_hour):
    start = datetime.combine(day, datetime.min.time(), ZONE).replace(hour=start_hour)
    end = start.replace(hour=end_hour)
    # Rain totals refer to the preceding three-hour interval. Include overlapping
    # intervals; temperature readings are coarse samples near the commute.
    selected = [e for e in entries if datetime.fromtimestamp(e['dt'], ZONE) > start
                and datetime.fromtimestamp(e['dt'], ZONE) - timedelta(hours=3) < end]
    if not selected:
        raise RuntimeError('No forecast coverage for this commute window.')
    feels = min(e['main']['feels_like'] for e in selected)
    temperatures = [e['main']['temp'] for e in selected]
    probability = max(e.get('pop', 0) for e in selected)
    wet = any(e.get('rain', {}).get('3h', 0) > 0 or
              e.get('snow', {}).get('3h', 0) > 0 for e in selected)
    wind = max(e.get('wind', {}).get('speed', 0) for e in selected) * 3.6
    clothing = []
    if feels < float(os.getenv('WARM_LAYER_BELOW_C', '12')):
        clothing.append('a warm layer')
    if feels < float(os.getenv('GLOVES_BELOW_C', '10')):
        clothing.append('gloves')
    if wet or probability >= float(os.getenv('RAIN_PROBABILITY_THRESHOLD', '0.4')):
        clothing.extend(['rain jacket', 'rain trousers'])
    if wind >= 25 and 'rain jacket' not in clothing:
        clothing.append('a wind-resistant jacket')
    return (f'{min(temperatures):.0f}–{max(temperatures):.0f} °C; feels as low as '
            f'{feels:.0f} °C; rain probability up to {probability:.0%}; '
            f'wind up to {wind:.0f} km/h.\nBring: '
            + ', '.join(clothing or ['your usual cycling clothes']) + '.')


def demo(day):
    entries = []
    for hour in (8, 11, 17, 20):
        stamp = datetime.combine(day, datetime.min.time(), ZONE).replace(hour=hour)
        evening = hour >= 17
        entries.append({'dt': int(stamp.timestamp()),
                        'main': {'temp': 11 if evening else 8,
                                 'feels_like': 9 if evening else 6},
                        'wind': {'speed': 5}, 'pop': 0.7 if evening else 0.1,
                        'rain': {'3h': 1.2} if evening else {}})
    return entries


def send_telegram(text):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise RuntimeError('Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.')
    request = Request('https://api.telegram.org/bot' + token + '/sendMessage',
                      data=urlencode({'chat_id': chat_id, 'text': text}).encode())
    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
        if not result.get('ok'):
            raise RuntimeError('Telegram did not confirm delivery.')
    except HTTPError as error:
        raise RuntimeError(f'Telegram returned HTTP {error.code}; check bot token and chat ID.') from None
    except (URLError, TimeoutError, ValueError):
        raise RuntimeError('Telegram delivery unconfirmed; check your chat before retrying.') from None
    print('Telegram delivery confirmed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Use fictional weather, no API key.')
    parser.add_argument('--send', action='store_true', help='Send the live forecast to Telegram.')
    args = parser.parse_args()
    if args.demo and args.send:
        parser.error('--demo cannot be combined with --send')
    load_env()
    now = datetime.now(ZONE)
    day = now.date()
    # A manual afternoon test should recommend tomorrow, not a past commute.
    if now.hour >= 10:
        day += timedelta(days=1)
    entries = demo(day) if args.demo else forecast()
    if args.demo:
        print('DEMO — fictional weather\n')
    parts = [f'Cycling forecast — {day:%a %d %b}']
    for label, start, end in [('To work', 8, 10), ('Home', 17, 20)]:
        parts.append(f'{label}, {start:02}:00–{end:02}:00\n' + recommend(entries, day, start, end))
    parts.append('Nearby three-hour forecasts, not exact rain timing. Weather: OpenWeather.')
    text = '\n\n'.join(parts)
    print(text)
    if args.send:
        send_telegram(text)



if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
