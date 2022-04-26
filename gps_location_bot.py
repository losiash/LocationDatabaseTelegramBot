#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopy.distance
import re
import requests
import sqlite3
import arrow
from SQlite_connection import *  # as sqlcon
from classes import * #
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import time



def get_dist(coord1, coord2):
    a = geopy.distance.distance(coord1, coord2).km
    if a<1:
        a = int(a*1000)
        return (f'{a} метров')
    a = round(a, 2)
    return (f'{a} км')

def nearest_point(coord):
    global location_coords
    dict_of_places={saved_coord:geopy.distance.distance(coord, saved_coord).km for saved_coord in location_coords if location_coords[saved_coord][0]}
    print(dict_of_places, "------------------------------------")

    return location_coords[min(dict_of_places, key=dict_of_places.get)][0]

def get_time(time):
    sec=time.seconds
    if sec<60: return [sec, "seconds"]
    elif sec<3600: return [sec//60, "minutes"]
    elif sec<86400: return [sec//3600, "hours"]
    elif sec<604800: return [sec//86400, "days"]
    else: return [sec//604800, "weeks"]



bot_key = "TOKEN"

users, dict_of_friends,location_coords = loading_from_database()

lat = ''
lon = ''




message_id_user = {}  #словарь вида -  номер сообщения - айди пользователя
slov = {}
users_chats = {}


def return_user(update):
    if users.get(update.message.chat.id):
        return users.get(update.message.chat.id)
    else:
        usr = new_user(update.message.chat)
        users[usr.id] = usr
        sql_add_user(update.message.chat)
        return usr


def help(update, context):

    send_message(context, update.message.chat.id, '''Команды: \n/generate_token - создает код подтверждения\n/friends - список друзей\n/gde - основная команда, показывающая расстояние до отслеживаемых людей.\n\nНажмите reply/ответить на сообщение с вашей локацией, введите название места, где вы находитесь''')
    print (update.message['chat'], "HELP")


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

    user = return_user(update)




def echo(update, context):
    global slov, users, dict_of_friends

    user = return_user(update)
    sec = update.message.date
    user.points_seconds[sec] = update.message.text

    print(update['message']['text'],"эхо апдейт")

    active_codes = [code for code,val in dict_of_friends.items() if val[2]]
    print(active_codes,"------------active_codes-------------")

    try:
      print(int(update['message']['text']) in active_codes)
      if int(update['message']['text']) in active_codes:
        if update.message.chat.id == users[dict_of_friends[int(update['message']['text'])][0]].id:
            send_message(context, update.message.chat.id, "вы не можете добавить себя в отслеживаемые")
        else:
            send_message(context, update.message.chat.id, f"now @{users[dict_of_friends[int(update['message']['text'])][0]].username} - added as new friend")
            sql_add_friend_rec( update.message.chat.id,int(update['message']['text']))
    except: pass


# def print_users(update, context):
#     list_of_usernames = [i.username for i in users.values()]
#     send_message(context, update.message.chat.id, str(list_of_usernames))

def print_friends(update, context):
    list_of_usernames = ['@'+users[x].username for x in get_friends(update.message.chat.id) if x]
    send_message(context, update.message.chat.id, ', '.join(list_of_usernames))

def get_friends(id):
    global dict_of_friends
    return list(set([val[1] for key,val in dict_of_friends.items() if val[0]==id] + [val[0] for key,val in dict_of_friends.items() if val[1]==id]))

def statistics(update, context):
    send_message(context, update.message.chat.id, "future update")

def generate_token(update, context):
    global dict_of_friends

    temp=17

    user = return_user(update)

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
        location_coords[(a.current_pos[0], a.current_pos[1])][0]=a.name
        sql_add_location(a.current_pos[0], a.current_pos[1],user_id=kod[0], message_id=kod[1], name=a.name)

        print (a, "NEW_NAME added by @", a.user)

def gde_ia(update, context):
    cur_user = return_user(update)
    if cur_user.current_location:
        send_message(context, update.message.chat.id, f"ближайшая к вам точка: {nearest_point(cur_user.current_location.current_pos)}")

    else:
        send_message(context, update.message.chat.id,
                     "мы не можем определить место, тк вы не прислали свою локацию: нажмите /help чтобы прочитать инструкцию")
    return


def gde(update, context):
    global  users
    gde_vse = []
    cur_user = return_user(update)
    # if not cur_user:
    #     return

    stroka = ''

    for user in users.values():
        if user.id in get_friends(cur_user.id):
             if user.current_location:
                if cur_user.current_location:
                    gde_vse.append([get_dist(cur_user.current_location.current_pos, user.current_location.current_pos), user.username,
                                    get_time(update.message.date-user.current_location.time_stamp), nearest_point(user.current_location.current_pos)])                    #user.current_location.name


                else:
                   send_message(context, update.message.chat.id, "we can’t determine the distance since you didn’t send your location")
                   return
             else:
               stroka += f"@{user.username} нет активной локации\n"
            #   stroka+=f"@{user.username} didn't send his location yet\n"



    for dist, name, last_update, name_of_loc in sorted(gde_vse):
        stroka+=f'@{name},   {str(dist)} -- {last_update[0]} {last_update[1]} ago, находился около {name_of_loc or "неизвестном месте"}\n'

    send_message(context, update.message.chat.id, stroka)




def get_location(update, context):

    print (update, "LOCATION_UPDATE")

    user=return_user(update)
    a = new_point(update,user)

    message= update.edited_message or update.message
    loc=message.location

    location_coords[(loc.latitude , loc.longitude)]=[None, user.id, message.message_id, message.forward_date or message.edit_date or message.date, message.date]
    sql_add_location(loc.latitude , loc.longitude,  user.id, message.message_id, name=None, time_stamp=message.forward_date or message.edit_date or message.date, message_date=message.date)


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
    dp.add_handler(CommandHandler("gde_ia", gde_ia))
    dp.add_handler(CommandHandler("statistics", statistics))
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
