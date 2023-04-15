import json
import time
import datetime
import threading
import random
import sqlite3
import telebot
import schedule
import geopy
import timezonefinder
import pytz
import requests
import config


# Initiating of the bot, start, help and city commands
bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=["start"])
def do_start(message="start"):
    """Asking user for his city."""
    bot.send_message(message.chat.id, text="Твой город?")


@bot.message_handler(commands=["help"])
def do_help(message="help"):
    """Sending info message."""
    bot.send_message(message.chat.id, text="\U000000B7 Чтобы получать прогноз погоды, напиши в чат название города где ты живешь.\n\U000000B7 Бот сообщит, удалось ли его сохранить, или возникли какие-то проблемы.\n\U000000B7 Чтобы напомнить (себе) какой у тебя сохранен город, вызови команду \"где я?!\".\n\U000000B7 Если уехал в другой город - просто напиши название нового места.\n\nThat's all folks!\n\n\U00002600\U0001F916\U00002600")


def query_city(user_id):
    """Get current user city from db, returns it."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''SELECT city
                 FROM users
                WHERE id = ?;'''
    q_data = [str(user_id)]
    
    try:
        with sql_connection:
            sql_cursor.execute(query, q_data)
            q_result = sql_cursor.fetchone()
    except sqlite3.Error as error:
        print("SQLite error:", error)
    finally:
        sql_connection.close()
    return q_result       


@bot.message_handler(commands=["city"])
def show_city(message="city"):
    """Calling func for current user city, send message with it."""
    user_id = message.from_user.id
    q_result = query_city(user_id)
    for city in q_result:
        the_city = city
    bot.reply_to(message, text=f"Твой город: {the_city}.")


# Below is for creating, updating and deleting users of the bot
def get_coords(user_city):
    """Get coordinates of user city, returns them."""
    try:
        geolocator = geopy.geocoders.Nominatim(user_agent="telebot")
        coords = geolocator.geocode(user_city)
        latitude = coords.latitude
        longitude = coords.longitude
    except AttributeError:
        latitude = None
        longitude = None
    return latitude, longitude


def get_timezone(latitude, longitude):
    """Get user time zone upon coordinates, returns it."""
    tzf = timezonefinder.TimezoneFinder()
    timezone = tzf.timezone_at(lat=latitude, lng=longitude)
    user_tzone = get_tz_hour(timezone)
    return user_tzone


def get_tz_hour(timezone):
    """Get user time zone hour upon its name, returns it."""
    dt = datetime.datetime.now()
    fmt = "%Y-%m-%d %H:%M:%S %Z%z"
    tz = pytz.timezone(timezone)
    localized = tz.localize(dt).strftime(fmt)
    tz_hour = localized[-5:-2]
    user_tzone = int(tz_hour)
    return user_tzone


def get_user_tzone(user_city):
    """Func to start process of user time zone getting, returns time zone."""
    latitude, longitude = get_coords(user_city)
    if latitude == None or longitude == None:
        user_tzone = None
    else:
        user_tzone = get_timezone(latitude, longitude)
    return user_tzone


def is_user_exist(user_id, user_name, user_city, user_tzone):
    """Check if user exists in db, returns success or not flag."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''SELECT *
                 FROM users 
                WHERE id = ?;'''
    q_data = [user_id]

    try:
        with sql_connection:
            sql_cursor.execute(query, q_data)
            q_result = sql_cursor.fetchall()
        if len(q_result) == 0:
            user_exists = False
        else:
            user_exists = True
    except sqlite3.Error as error:
        user_exists = None
        print("SQLite error:", error)
    finally:
        sql_connection.close()
    return user_exists


def create_user(user_id, user_name, user_city, user_tzone):
    """Create new user in db, return succes or nor flag."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''INSERT INTO users(id, name, city, zone)
                    VALUES (?, ?, ?, ?);'''
    q_data = [user_id, user_name, user_city, user_tzone]

    try:
        with sql_connection:
            sql_cursor.execute(query, q_data)
            sql_connection.commit()
            user_created = True
    except sqlite3.Error as error:
        user_created = False
        print("SQLite error:", error)
    finally:
        sql_connection.close()
    return user_created


def update_user(user_id, user_name, user_city, user_tzone):
    """Update existing user data in db, returns success or not flag."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''UPDATE users
                  SET name = ?,
                      city = ?,
                      zone = ?
                WHERE id = ?;'''
    q_data = [user_name, user_city, user_tzone, user_id]
    
    try:
        with sql_connection:
            sql_cursor.execute(query, q_data)
            sql_connection.commit()
            user_updated = True
    except sqlite3.Error as error:
        user_updated = False
        print("SQLite error:", error)
    finally:
        sql_connection.close()
    return user_updated


def delete_user(user_id):
    """Delete inactive user from db."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''DELETE FROM users
                     WHERE id = ?;'''
    q_data = [user_id]

    try:
        with sql_connection:
            sql_cursor.execute(query, q_data)
            sql_connection.commit()
    except sqlite3.Error as error:
        print("SQLite error:", error)
    finally:
        sql_connection.close()


@bot.message_handler(content_types=["text"])
def get_user_data(message):
    """Getting user data, calling for create or update user funcs."""
    user_id = message.from_user.id
    user_city = message.text
    user_name = str(message.from_user.first_name) + " " + str(message.from_user.last_name) + " " + str(message.from_user.username)
    
    user_tzone = get_user_tzone(user_city)
    if user_tzone == None:
        bot.reply_to(message, text="Город не найден, попробуй еще раз.")
    else:
        user_exists = is_user_exist(user_id, user_name, user_city, user_tzone)
        if user_exists == None:
            bot.reply_to(message, text="Упс, ошибочка... Попробуй еще раз.")
        elif user_exists == False:
            user_created = create_user(user_id, user_name, user_city, user_tzone)
            if user_created:
                bot.reply_to(message, text="Сохранил!")
            else:
                bot.reply_to(message, text="Упс, ошибочка... Попробуй еще раз.")
        else:
            user_updated = update_user(user_id, user_name, user_city, user_tzone)
            if user_updated:
                bot.reply_to(message, text="Сохранил!")
            else:
                bot.reply_to(message, text="Упс, ошибочка... Попробуй еще раз.")


# Below is for preparing and sending forecast
def get_wish(wishes):
    """Recieve the list of wishes, choose and returns one of them."""
    star_wars = "05-04"
    womans_day = "03-08"
    raw_date = datetime.date.today()
    str_date = raw_date.strftime("%m-%d")

    if str_date == star_wars:
        the_wish = wishes[4]
    elif str_date == womans_day:
        the_wish = wishes[5]
    else:
        the_wish = random.choice(wishes)
    return the_wish


def query_all_data():
    """Query users data from db, returns list of tuples."""
    sql_connection = sqlite3.connect(config.database)
    sql_cursor = sql_connection.cursor()
    query = '''SELECT *
                 FROM users;'''
    
    try:
        with sql_connection:
            sql_cursor.execute(query)
            q_result = sql_cursor.fetchall()
    except sqlite3.Error as error:
        print("SQLite error:", error)
    finally:
        sql_connection.close()
    return q_result       


def look_for_recipients(users_data):
    """Definend users for processing, returns the list of them."""
    raw_time = datetime.datetime.now()
    str_time = raw_time.strftime("%H")
    recipients = []

    for user in users_data:
        if (user[3] + int(str_time) == 8) or ((user[3] + int(str_time)) - 8 == 24):
            recipients.append([user[0], user[2]])
        else:
            pass
    return recipients


def get_weather(the_wish, latitude, longitude):
    """Do request for weather, returns complete message for user."""
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&exclude=minutely,hourly,alerts&appid={config.openweathermap_token}&units=metric&lang=ru")
    weather_data = json.loads(response.text)
    night_t = round(weather_data["daily"][0]["temp"]["night"])
    morning_t = round(weather_data["daily"][0]["temp"]["morn"])
    day_t = round(weather_data["daily"][0]["temp"]["day"])
    evening_t = round(weather_data["daily"][0]["temp"]["eve"])
    night_t_fl = round(weather_data["daily"][0]["feels_like"]["night"])
    morning_t_fl = round(weather_data["daily"][0]["feels_like"]["morn"])
    day_t_fl = round(weather_data["daily"][0]["feels_like"]["day"])
    evening_t_fl = round(weather_data["daily"][0]["feels_like"]["eve"])
    wind = round(weather_data["daily"][0]["wind_speed"])
    wind_gust = round(weather_data["daily"][0]["wind_gust"])
    chance_of_precipitation = int(weather_data["daily"][0]["pop"]) * 100
    condition = weather_data["daily"][0]["weather"][0]["description"]
    the_message = f"Сегодня <b>{condition.lower()}</b>:\n\U0001F321 Температура [по ощущениям]:\n        \U000000B7 ночью {night_t}\N{DEGREE SIGN}C [{night_t_fl}\N{DEGREE SIGN}C]\n        \U000000B7 утром {morning_t}\N{DEGREE SIGN}C [{morning_t_fl}\N{DEGREE SIGN}C]\n        \U000000B7 днём {day_t}\N{DEGREE SIGN}C [{day_t_fl}\N{DEGREE SIGN}C]\n        \U000000B7 вечером {evening_t}\N{DEGREE SIGN}C [{evening_t_fl}\N{DEGREE SIGN}C]\n\U0001F32C Скорость ветра {wind}м/с, порывы {wind_gust}м/с\n\U0001F327 Вероятность осадков {chance_of_precipitation}%\n\n{the_wish}"
    return the_message


def send_message(user_id, the_message):
    """Send message to user, or calling delete func."""
    try:
        bot.send_message(chat_id=user_id, text=the_message, parse_mode="html")
    except telebot.apihelper.ApiTelegramException:
        delete_user(user_id=user_id)


def bot_job():
    """Func for calling other funcs in the sake of main bot purpose."""
    the_wish = get_wish(wishes=config.wishes)

    users_data = query_all_data()
    recipients = look_for_recipients(users_data)

    for recipient in recipients:
        user_id = recipient[0]
        user_city = recipient[1]
        latitude, longitude = get_coords(user_city)
        the_message = get_weather(the_wish, latitude, longitude)
        send_message(user_id, the_message)


# Below is for scheduling jobs and running the bot
schedule.every().hour.at(":01").do(bot_job)


if __name__ == '__main__':
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        schedule.run_pending()
        time.sleep(1)
