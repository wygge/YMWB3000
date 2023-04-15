Hi folks!


This is repo of my Telegram weather forecast bot. So, what does this bot do?

1. Register user and stores data in SQLite3 database:
    - stores user Telegam ID as user ID for database;
    - stores user names (Telegram name and username);
    - stores user city of living;
    - calculate and stores user timezone hour;

2. Update user data.
If user moves to another city and text about it to bot, bot will also look up for changes in user's name and username.

3. Delete user.
If user stoppes the bot, it will delete his data from database during next process cycle (below The Process is described).

4. Send to user weather forecast (The Process).
Everyday at 08:01am bot send message to user with weather forecast for a day according to user currently stored city name.
In addition, as he is a cute little droid, he provides some good words to user to make morning a little bit warmer. So cute!


External libs that bot use:
- schedule for scheduling The Process;
- pytz and timezonefinder for calculating timezonehour;
- geopy for calculating user coordinates (long and lat are used for forecast request);
- requests for forecast requests;
- PyTelegramBotAPI for telegram bot instance;


Finally, bot use OpenWeather (https://openweathermap.org) for weather forecasts.


You are welcome to connect via https://t.me/YMWB3000_bot


That's all, folks!