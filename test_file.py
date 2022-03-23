#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopy.distance
import re
import requests
import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import datetime


def get_dist(coord1, coord2):
    a = geopy.distance.distance(coord1, coord2).km
    if a < 1:
        a = int(a * 1000)
        return (f'{a} метров')
    a = round(a, 2)
    return (f'{a} км')


users = {}
obr_users = {}

bot_key = "TOKEN"

lat = ''
lon = ''

conn = sqlite3.connect('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\orders.db')
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
   userid INT PRIMARY KEY,
   username TEXT);
""")

cur.execute("""CREATE TABLE IF NOT EXISTS friends_graph(
   verification_code INT PRIMARY KEY,
   userid_sender INT,
   userid_reciver INT);
""")

cur.execute("""CREATE TABLE IF NOT EXISTS location_database(
   user_id INT PRIMARY KEY,
   date/time TEXT,
   lon FLOAT,
   lat FLOAT);
""")

conn.commit()

file_log = open('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\telegram_bot_log.txt', 'w',
                buffering=1)

message_id_user = {}  # словарь вида -  номер сообщения - айди пользователя
slov = {}
users_chats = {}


def sql_add_user(username, userid):
    cur.execute("INSERT INTO users VALUES(?, ?);", (userid, username))
    conn.commit()


def sql_add_location(id, time, ln, lt):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (id, time, ln, lt))
    conn.commit()


def sql_add_friend(id1, id2, ver_code):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (ver_code, id1, id2))
    conn.commit()


def help(update, context):
    print(update.message['chat'])
    print(update.message)


def send_message(context, chat_id, text, popitka=0):
    try:
        context.bot.send_message(chat_id, text)
    except:
        if popitka < 6:
            time.sleep(1 + popitka)
            popitka += 1
            return send_message(context, chat_id, text, popitka)
        else:
            print('ответ не удалось отправить!')
            return False
    if popitka != 0:
        print('ответ отправлен!')

    return True


def start(update, context):
    message = update.message['text']
    print(message)

    send_message(context, chat_id=update.effective_chat.id,
                 text='Привет! Отправьте сюда свое местоположение или livelocation, a потом наберите команду /gde')

    user = new_user(update.message['chat'])


class new_point:
    def __init__(self, update):
        global users, file_log

        message = update.edited_message or update.message
        location = message.location
        self.name = None
        self.current_pos = (location.latitude, location.longitude)
        self.horizontal_accuracy = None or location.horizontal_accuracy
        self.heading = None or location.heading
        self.time_stamp = message.forward_date or message.edit_date or message.date
        self.message_date = message.date
        self.user = users.get(message.chat.id) or new_user(message.chat)
        self.kod = (self.user.id, message.message_id)
        self.live_period = None or location.live_period
        self.user.current_location = self.current_pos
        self.write_file()
        print(self)

    def __str__(self):
        return f'{self.time_stamp}, {self.name}, {self.kod}, {self.current_pos}, {self.horizontal_accuracy}, {self.heading}'

    def write_file(self):
        file_log.write(
            f'{self.time_stamp}\t{self.kod}\t{self.current_pos}\t{self.heading}\t{self.horizontal_accuracy}\t{self.live_period}\n')


class new_track:
    def __init__(self, point):
        self.name = ''
        self.points = [point]
        self.start_time = point.message_date
        self.live_period = point.live_period
        self.finish_time = self.start_time + datetime.timedelta(0, self.live_period)
        print(self.finish_time)
        print(self)

    def add_point(self, point):
        self.points.append(point)

    def __str__(self):
        return str(self.name) + ' ' + str([x.current_pos for x in self.points])


class new_user:
    def __init__(self, chat):
        global users, obr_users, file_log
        self.username = chat['username']
        self.current_location = None
        self.id = chat['id']
        self.first_name = chat['first_name']
        self.last_name = chat['last_name']
        self.points = {}
        self.points_seconds = {}
        self.tracks = {}
        users[self.id] = self
        obr_users[self.first_name] = self.id
        print('Новый пользователь: ', self)
        self.write_file()

    def write_file(self):
        print('входим в процедуру')
        file_log.write(f'{self.id}\t{self.first_name}\t{self.last_name}\t{self.username}\n')

    def __str__(self):
        return f'user_id: {self.id},  username: {self.username}, first_name: {self.first_name}, last_name: {self.last_name}'


def echo(update, context):
    global slov, users
    print(update)
    user = users.get(update.message.chat.id) or new_user(update.message.chat)
    sec = update.message.date
    user.points_seconds[sec] = update.message.text

    return


def get_reply(update, context):
    reply = update.message.reply_to_message
    user_id = reply.chat.id
    kod = (user_id, reply.message_id)
    if not user_id in users:
        return
    user = users[user_id]
    a = user.points.get(kod) or user.tracks.get(kod)
    if a:
        a.name = update.message.text
        print(a)


def gde(update, context):
    global users, file_log
    gde_vse = []
    cur_user = users.get(update.message.chat.id)
    file_log.write(f'gde\t{str(update.message.chat.id)}\n')
    if not cur_user:
        return

    for user in users.values():
        gde_vse.append([get_dist(cur_user.current_location, user.current_location), user.username])
        print(user.username, get_dist(cur_user.current_location, user.current_location))
    stroka = ''
    for dist, name in sorted(gde_vse):
        stroka += f'@{name},   {str(dist)}\n'

    send_message(context, update.message.chat.id, stroka)


def get_location(update, context):
    print(update)
    a = new_point(update)
    if a.live_period:  # если у нас лайв.локейшн
        if a.kod not in a.user.tracks:  # если новый лайв.локейшн
            a.user.tracks[a.kod] = new_track(a)
        else:
            a.user.tracks[a.kod].add_point(a)  # добавляем точку к трэку
            print(a.user.tracks[a.kod])

    else:
        a.user.points[
            a.kod] = a  # если обычная точка,то добавляем пользователю в словарь его точек (код_пользователя + код_сообщения: объект класса точка)
        a.name = a.user.points_seconds.get(a.message_date,
                                           f'New point {len(a.user.points)}')  # присваем имя точки, если оно было задано при форвардинге
        print(a.user.points)


def error(update, context):
    user_says = " ".join(context.args)
    update.message.reply_text("You said: " + user_says)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    global bot_key
    request_kwargs = {}
    updater = Updater(bot_key, request_kwargs=request_kwargs)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("gde", gde))

    # on noncommand i.e message - echo the message on Telegram

    location_handler = MessageHandler(Filters.location, get_location)
    dp.add_handler(location_handler)

    reply_handler = MessageHandler(Filters.reply, get_reply)
    dp.add_handler(reply_handler)  # для того, чтобы задавать названия точкам и трекам

    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    echo_handler = MessageHandler(~Filters.command, echo)
    dp.add_handler(echo_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

#-------------------------------------------------------------------------------------------------------

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopy.distance
import re
import requests
import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import datetime



def get_dist(coord1, coord2):
    a = geopy.distance.distance(coord1, coord2).km
    if a<1:
        a = int(a*1000)
        return (f'{a} метров')
    a = round(a, 2)
    return (f'{a} км')


users = {}
obr_users = {}

bot_key = "TOKEN"


lat = ''
lon = ''

conn = sqlite3.connect('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\tgbot_database.db', check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
   userid INT PRIMARY KEY,
   username TEXT,
   first_name TEXT,
   second_name TEXT);
""")

cur.execute("""CREATE TABLE IF NOT EXISTS friends_graph(
   verification_code INT PRIMARY KEY,
   userid_sender INT,
   userid_receiver INT,
   active BOOLEAN);
""")

cur.execute("""CREATE TABLE IF NOT EXISTS location_database(
   user_id INT PRIMARY KEY,
   date_time TEXT,
   lon FLOAT,
   lat FLOAT);
""")

conn.commit()



file_log = open('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\telegram_bot_log.txt','w', buffering=1)


message_id_user = {}  #словарь вида -  номер сообщения - айди пользователя
slov = {}
users_chats = {}
dict_of_friends={}   #словарь вида -  айди пользователя - массив айди его друзей

# def user_get_info(chat):
#     return (chat['id'],chat['username'],chat['first_name'],chat['last_name'])

def sql_add_user(chat):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (chat['id'], chat['username'], chat['first_name'], chat['last_name']))
    conn.commit()

def sql_add_location(id, time, ln , lt):
    cur.execute("INSERT INTO location_database VALUES(?, ?, ?, ?);", (id, time, ln ,lt))
    conn.commit()

def sql_add_friend_send(id1, ver_code):
    dict_of_friends[ver_code]=(id1, None, True)
    cur.execute("INSERT INTO friends_graph VALUES(?, ?, ?, ?);", (ver_code, id1, None, True))
    conn.commit()

def sql_add_friend_rec(id2, ver_code):
    dict_of_friends[ver_code]=(dict_of_friends[ver_code][0],id2,False)
    cur.execute(f"UPDATE friends_graph SET userid_receiver = {id2}  WHERE verification_code = {ver_code};")
    cur.execute(f"UPDATE friends_graph SET  active = {False}  WHERE verification_code = {ver_code};")
    conn.commit()


def loading_from_database():
    global dict_of_friends

    # USERS
    cur.execute("SELECT * FROM users;")
    old_users = cur.fetchall()
    mask=('id', 'username', 'first_name', 'last_name')

    for usr in old_users:
        user=new_user({mask[0]:usr[0], mask[1]:usr[1], mask[2]:usr[2], mask[3]:usr[3]}, False)

    print(old_users, "old users")

    # GRAPH_OF_FRIENDS

    cur.execute("SELECT * FROM friends_graph")
    table = cur.fetchall()

    for agreement in table:
        dict_of_friends[agreement[0]]=(agreement[1],agreement[2],agreement[3])

    print(dict_of_friends, "old friends")

    # LOCATION_DATABASE

def help(update, context):

    print (update.message['chat'])
    print (update.message)



def send_message(context, chat_id, text, popitka=0):
    try:
        context.bot.send_message(chat_id, text)
    except:
        if popitka<6:
            time.sleep(1+popitka)
            popitka+=1
            return send_message(context, chat_id, text, popitka)
        else:
            print('ответ не удалось отправить!')
            return False
    if popitka!=0:
        print ('ответ отправлен!')

    return True



def start(update, context):
    message = update.message['text']
    print(message)

    send_message(context, chat_id=update.effective_chat.id,
                             text='Привет! Отправьте сюда свое местоположение или livelocation, a потом наберите команду /gde')

    user = new_user(update.message['chat'], True)


class new_point:
    def __init__(self, update):
        global users, file_log

        message = update.edited_message or update.message
        location = message.location
        self.name = None
        self.current_pos = (location.latitude, location.longitude)
        self.horizontal_accuracy = None or location.horizontal_accuracy
        self.heading = None or location.heading
        self.time_stamp = message.forward_date or message.edit_date or message.date
        self.message_date = message.date
        self.user = users.get(message.chat.id) or new_user(message.chat, True)
        self.kod = (self.user.id,message.message_id)
        self.live_period = None or location.live_period
        self.user.current_location = self.current_pos
#        self.write_file()
        print (self)

    def __str__(self):
        return  f'{self.time_stamp}, {self.name}, {self.kod}, {self.current_pos}, {self.horizontal_accuracy}, {self.heading}'

    # def write_file(self):
    #     file_log.write(f'{self.time_stamp}\t{self.kod}\t{self.current_pos}\t{self.heading}\t{self.horizontal_accuracy}\t{self.live_period}\n')


class new_track:
    def __init__(self, point):
        self.name = ''
        self.points = [point]
        self.start_time = point.message_date
        self.live_period = point.live_period
        self.finish_time = self.start_time + datetime.timedelta(0, self.live_period)
        print (self.finish_time)
        print (self)
    def add_point(self, point):
        self.points.append(point)
    def __str__(self):
        return str(self.name) +' ' + str([x.current_pos for x in self.points])



class new_user:
    def __init__(self, chat, check_new_user):
        global users, obr_users, file_log
        self.username = chat['username']
        self.current_location = None
        self.id = chat['id']
        self.first_name = chat['first_name']
        self.last_name = chat['last_name']
        self.points = {}
        self.points_seconds = {}
        self.tracks = {}
        users[self.id] = self
        obr_users[self.first_name] = self.id
        print (f'{"Новый" if check_new_user else "Старый"} пользователь: ', self)
        if check_new_user:
          sql_add_user(chat)
        # self.write_file()



    def __str__(self):
        return f'user_id: {self.id},  username: {self.username}, first_name: {self.first_name}, last_name: {self.last_name}'

def echo(update, context):
    global slov, users
    print (update)
    user = users.get(update.message.chat.id) or new_user(update.message.chat, True)
    sec = update.message.date
    user.points_seconds[sec] = update.message.text

    print(update['message']['text'],"эхо апдейт")

    # cur.execute(f"SELECT * FROM friends_graph WHERE active={True}")
    # alnfo=cur.fetchall()
    # print(alnfo, "Активные")
    # active_codes = [a for (a,b,c,d) in alnfo]

    active_codes = [code for code,val in dict_of_friends.items() if val[2]]
    print(active_codes,"-------------------------")

    try:
      print(int(update['message']['text']) in active_codes)
      if int(update['message']['text']) in active_codes:
        send_message(context, update.message.chat.id, f"now @{users[dict_of_friends[int(update['message']['text'])][0]].username} - added as new friend")
        sql_add_friend_rec( update.message.chat.id,int(update['message']['text']))
    except: pass


# def print_users0(update, context):
#     list_of_id = [i for i in users]
#     print(list_of_id)
#     sl_id_name={}
#     for id in list_of_id:
#         cur.execute(f"SELECT * FROM users WHERE users.userid = {id}")
#         sl_id_name[id] = cur.fetchone()
#
#
#     send_message(context, update.message.chat.id, str( list(sl_id_name.values() )))


def print_users(update, context):
    list_of_usernames = [i.username for i in users.values()]
    send_message(context, update.message.chat.id, str(list_of_usernames))

def print_friends(update, context):
    list_of_usernames = ['@'+users[x].username for x in get_friends(update.message.chat.id)]
    send_message(context, update.message.chat.id, ', '.join(list_of_usernames))

def get_friends(id):
    global dict_of_friends
    return list(set([val[1] for key,val in dict_of_friends.items() if val[0]==id] + [val[0] for key,val in dict_of_friends.items() if val[1]==id]))

def generate_token(update, context):
    temp=17

    # cur.execute("SELECT * FROM friends_graph;")
    # all_info=cur.fetchall()
    # print(all_info, "all information")
    # all_tokens = [a for (a,b,c,d) in all_info]
    # print(all_tokens, "all tokens")

    all_tokens = list(dict_of_friends.keys())

    if all_tokens:
       new_token=max(all_tokens)+temp
    else:
       new_token=123456

    sql_add_friend_send(update.message.chat.id, new_token)
    send_message(context, update.message.chat.id, f"send this token to your friend: {new_token}")




def get_reply(update, context):
    reply = update.message.reply_to_message
    user_id = reply.chat.id
    kod = (user_id, reply.message_id)
    if not user_id in users:
        return
    user = users[user_id]
    a = user.points.get(kod) or user.tracks.get(kod)
    if a:
        a.name = update.message.text
        print (a)


def gde(update, context):
    global  users, file_log
    gde_vse = []
    cur_user = users.get(update.message.chat.id)
    # file_log.write(f'gde\t{str(update.message.chat.id)}\n')
    if not cur_user:
        return


    for user in users.values():
        if user.id in get_friends(update.message.chat.id):
            gde_vse.append([get_dist(cur_user.current_location, user.current_location), user.username])
            print (user.username, get_dist(cur_user.current_location, user.current_location))

    stroka = ''
    for dist, name in sorted(gde_vse):
        stroka+=f'@{name},   {str(dist)}\n'

    send_message(context, update.message.chat.id, stroka)




def get_location(update, context):
    print (update)
    a = new_point(update)
    if a.live_period:  # если у нас лайв.локейшн
        if a.kod not in a.user.tracks:  # если новый лайв.локейшн
            a.user.tracks[a.kod] = new_track(a)
        else:
            a.user.tracks[a.kod].add_point(a)  # добавляем точку к трэку
            print (a.user.tracks[a.kod])

    else:
        a.user.points[a.kod] = a   # если обычная точка,то добавляем пользователю в словарь его точек (код_пользователя + код_сообщения: объект класса точка)
        a.name = a.user.points_seconds.get(a.message_date, f'New point {len(a.user.points)}')   # присваем имя точки, если оно было задано при форвардинге
        print (a.user.points)




def error(update, context):
    user_says = " ".join(context.args)
    update.message.reply_text("You said: " + user_says)



def main():
    # other
    loading_from_database()

    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    global bot_key
    request_kwargs = {}
    updater = Updater(bot_key, request_kwargs=request_kwargs)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("gde", gde))
    dp.add_handler(CommandHandler("generate_token", generate_token))

    # admin commands
    dp.add_handler(CommandHandler("friends", print_friends))
    #dp.add_handler(CommandHandler("print_users", print_users))
    # on noncommand i.e message - echo the message on Telegram

    location_handler = MessageHandler(Filters.location, get_location)
    dp.add_handler(location_handler)

    reply_handler = MessageHandler(Filters.reply, get_reply)
    dp.add_handler(reply_handler)   # для того, чтобы задавать названия точкам и трекам



    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    echo_handler = MessageHandler(~Filters.command, echo)
    dp.add_handler(echo_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()



if __name__ == '__main__':
    main()

file_log.close()
