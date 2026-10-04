# Commute weather assistant

A Python project for Amsterdam cycling commutes: 08:00–10:00 and
17:00–20:00. Forecast previews and scheduled Telegram clothing recommendations.

## Run without credentials

Python 3.11 or newer; no packages required:

```sh
python bot.py --demo
```

Demo weather is fictional. Read `recommend()` to understand the clothing rules.

## Live preview

Copy `.env.example` to `.env`, then set a newly generated OpenWeather key.
Never commit `.env`. Revoke real credentials exposed in earlier commits;
removing them from the current source does not invalidate them.

```sh
python bot.py
```

Uses the 5-day/3-hour forecast, metric units, and Europe/Amsterdam time.
Includes precipitation intervals overlapping each commute window. Temperature
and wind are coarse forecast samples. Max rain probability is not a cumulative
probability. Thresholds are adjustable starting assumptions, not personalised
validated advice. Default location is Amsterdam city centre.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Next milestones

1. Verify a live forecast preview.
2. Add Telegram delivery with explicit send mode and delivery logging.
3. Schedule one weekday message at 07:00 Europe/Amsterdam on Paint.
4. Add feedback and refine clothing rules.

Telegram delivery and GitHub Actions scheduling are now included.

## GitHub Actions deployment

The included workflows run tests on code changes and send the forecast at
07:00 Europe/Amsterdam on weekdays. Add repository Actions secrets named
OPENWEATHER_API_KEY, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
Run "Morning cycling weather" manually from Actions to test delivery.
Manual runs after 10:00 use tomorrow's forecast; morning runs use today.
Scheduled runs can be delayed or dropped by GitHub, and public repository
schedules disable after 60 days without repository activity.
No automatic delivery retries or cross-run deduplication are implemented.
Concurrent executions are queued, but manual reruns can send another message.
