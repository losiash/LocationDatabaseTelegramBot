#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopy.distance
import re
import requests
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

file_log = open('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\telegram_bot_log.txt','w', buffering=1)


message_id_user = {}  #словарь вида -  номер сообщения - айди пользователя
slov = {}
users_chats = {}




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
        self.kod = (self.user.id,message.message_id)
        self.live_period = None or location.live_period
        self.user.current_location = self.current_pos
        self.write_file()
        print (self)

    def __str__(self):
        return  f'{self.time_stamp}, {self.name}, {self.kod}, {self.current_pos}, {self.horizontal_accuracy}, {self.heading}'

    def write_file(self):
        file_log.write(f'{self.time_stamp}\t{self.kod}\t{self.current_pos}\t{self.heading}\t{self.horizontal_accuracy}\t{self.live_period}\n')


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
        print ('Новый пользователь: ', self)
        self.write_file()

    def write_file(self):
        print ('входим в процедуру')
        file_log.write(f'{self.id}\t{self.first_name}\t{self.last_name}\t{self.username}\n')




    def __str__(self):
        return f'user_id: {self.id},  username: {self.username}, first_name: {self.first_name}, last_name: {self.last_name}'

def echo(update, context):
    global slov, users
    print (update)
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
        print (a)


def gde(update, context):
    global  users, file_log
    gde_vse = []
    cur_user = users.get(update.message.chat.id)
    file_log.write(f'gde\t{str(update.message.chat.id)}\n')
    if not cur_user:
        return


    for user in users.values():
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
    dp.add_handler(reply_handler)   # для того, чтобы задавать названия точкам и трекам



    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    echo_handler = MessageHandler(~Filters.command, echo)
    dp.add_handler(echo_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()