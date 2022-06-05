#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopy.distance
import requests
import secrets
from SQlite_connection import *  # as sqlcon
from classes import *
import string
import time


from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = 'token'
alphabet = string.ascii_letters + string.digits


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
import random


btn_gde = KeyboardButton('/gde')
btn_friends = KeyboardButton('/friends')
btn_token = KeyboardButton('/token')
btn_gde_ya = KeyboardButton('/gde_ya')
btn_help = KeyboardButton('/help')

mainMenu =  ReplyKeyboardMarkup(resize_keyboard = True).add(btn_gde, btn_friends, btn_token, btn_gde_ya, btn_help)


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):

    print(message.text)
    # await bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}', reply_markup=mainMenu)
    await bot.send_message(message.from_user.id, f'Привет! Отправьте сюда свое местоположение или livelocation, '
                                                 f' потом наберите команду /gde', reply_markup=mainMenu)

    user = return_user(message)


@dp.message_handler(commands=['token'])
async def command_token(message):
    global dict_of_friends

    user = return_user(message)

    new_token = ''.join(secrets.choice(alphabet) for i in range(8))


    sql_add_friend_send(message.from_user.id, new_token)
    dict_of_friends[new_token]=(message.from_user.id, None, True)

    await bot.send_message(message.from_user.id, f"отправьте этот токен своему другу: {new_token}", reply_markup=mainMenu)

@dp.message_handler(commands=['friends'])
async def command_friends(message):
    list_of_usernames = ['@'+users[x].username for x in get_friends(message.from_user.id) if x]
    await bot.send_message(message.from_user.id, ', '.join(list_of_usernames), reply_markup=mainMenu)


def get_friends(id):
    global dict_of_friends
    return list(set([val[1] for key,val in dict_of_friends.items() if val[0]==id] + [val[0] for key,val in dict_of_friends.items() if val[1]==id]))



@dp.message_handler(commands=['help'])
async def command_help(message: types.Message):

    print(message.text)
    # await bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}', reply_markup=mainMenu)
    await bot.send_message(message.from_user.id, 'Команды: \n/token - создает код подтверждения\n/friends - список друзей\n/gde - основная команда, показывающая расстояние до отслеживаемых людей.\n\nНажмите reply/ответить на сообщение с вашей локацией, введите название места, где вы находитесь',  reply_markup=mainMenu)
    print (message, "HELP")

@dp.message_handler(commands=['gde_ya'])
async def command_gde_ya(message):
    cur_user = return_user(message)
    if cur_user.current_location:
        await bot.send_message(message.from_user.id,f"ближайшая к вам точка: {nearest_point(cur_user) or 'неизвестное место'}",
                               reply_markup=mainMenu)
    else:
        await bot.send_message(message.from_user.id,"мы не можем определить место, так как вы не прислали свою геолокацию: нажмите /help чтобы прочитать инструкцию",
                               reply_markup=mainMenu)

    return



@dp.message_handler(commands=['gde'])
async def command_gde(message: types.Message):
    global  users
    gde_vse = []
    cur_user = return_user(message)

    print (message)

    stroka = ''


    for user in users.values():
        if user.id in get_friends(cur_user.id):
             if user.current_location:
                if cur_user.current_location:
                    gde_vse.append([get_dist(cur_user.current_location.current_pos, user.current_location.current_pos), user.username,
                                    get_time(message.date-user.current_location.time_stamp), nearest_point(user)]) #user.current_location.name


                else:
                   await bot.send_message(message.from_user.id, "мы не можем определить расстояние, так как вы не прислали свою геолокацию", reply_markup=mainMenu)

             else:
               stroka += f"@{user.username} нет активной геолокации\n"




    for dist, name, last_update, name_of_loc in sorted(gde_vse):
        stroka+=f'@{name},   {str(dist)} -- {last_update[0]} {last_update[1]} назад, находился около {name_of_loc or "неизвестном месте"}\n'


    await bot.send_message(message.from_user.id, stroka, reply_markup=mainMenu)


@dp.message_handler(content_types=['location'])
async def get_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    # reply = "latitude:  {}\nlongitude: {}".format(lat, lon)
    # await message.answer(reply, reply_markup=types.ReplyKeyboardRemove())

    print (message, "LOCATION_UPDATE")

    user=return_user(message)
    a = new_point(message,user)

    # message= update.edited_message or update.message
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







def get_dist(coord1, coord2):
    a = geopy.distance.distance(coord1, coord2).km
    if a<1:
        a = int(a*1000)
        return (f'{a} метров')
    a = round(a, 2)
    return (f'{a} км')

def nearest_point(user):
    coord=user.current_location.current_pos
    friends=get_friends(user.id)

    global location_coords
    dict_of_places={saved_coord:geopy.distance.distance(coord, saved_coord).km
                    for saved_coord in location_coords if (location_coords[saved_coord][0] and
                                                           (location_coords[saved_coord][1] in friends or not location_coords[saved_coord][1]))}
    print(dict_of_places, "------------------------------------")

    if min(dict_of_places.values())>2:
        return
    else:
        return location_coords[min(dict_of_places, key=dict_of_places.get)][0]

def get_time(time):
    sec=time.seconds
    if sec<60: return [sec, "секунд"]
    elif sec<3600: return [sec//60, "минут"]
    elif sec<86400: return [sec//3600, "часов"]
    elif sec<604800: return [sec//86400, "дней"]
    else: return [sec//604800, "недель"]




users, dict_of_friends,location_coords = loading_from_database()

lat = ''
lon = ''




message_id_user = {}  #словарь вида -  номер сообщения - айди пользователя
slov = {}
users_chats = {}


def return_user(message):
    if users.get(message.from_user.id):
        return users.get(message.from_user.id)
    else:
        message_dict = {'username':message.from_user.username, 'id':message.from_user.id, 'first_name':message.from_user.first_name, 'last_name':message.from_user.last_name}
        usr = new_user(message_dict)
        users[usr.id] = usr
        sql_add_user(message_dict)
        return usr






@dp.message_handler()
async def bot_message(message: types.Message):
    global slov, users, dict_of_friends

    if reply:=message.reply_to_message:
        user_id = reply.chat.id
        kod = (user_id, reply.message_id)
        if not user_id in users:
            return
        user = users[user_id]
        a = user.points.get(kod) or user.tracks.get(kod)
        if a:
            a.name = message.text
            location_coords[(a.current_pos[0], a.current_pos[1])][0] = a.name
            sql_add_location(a.current_pos[0], a.current_pos[1], user_id=kod[0], message_id=kod[1], name=a.name)

            print(a, "NEW_NAME added by @", a.user)
        return


    user = return_user(message)
    # sec = message.date
    # user.points_seconds[sec] = update.message.text

    print(message.text,"эхо апдейт")

    active_codes = [str(code) for code,val in dict_of_friends.items() if val[2]]
    availability_check= [x for x in active_codes if x in message.text]

    if availability_check:
        rec_token=availability_check[0]
        friend = users[dict_of_friends[rec_token][0]]
        print(dict_of_friends,[friend.id,message.from_user.id,False])

        if message.from_user.id  == friend.id:
            await bot.send_message(message.from_user.id,  'вы не можете добавить себя в отслеживаемые',   reply_markup=mainMenu)

        elif (friend.id,message.from_user.id,False) in [val for code,val in dict_of_friends.items() if not val[2]]:
            await bot.send_message(message.from_user.id,  'вы уже в отслеживаемых с этим человеком',   reply_markup=mainMenu)

        elif (message.from_user.id,friend.id,False) in [val for code,val in dict_of_friends.items() if not val[2]]:
            await bot.send_message(message.from_user.id,  'вас уже добавили в отслеживаемые',   reply_markup=mainMenu)

        else:
            await bot.send_message(message.from_user.id,  f"now @{friend.username} - added as new friend",   reply_markup=mainMenu)
            await bot.send_message(friend.id,  f"now @{message.from_user.username} - added as new friend",   reply_markup=mainMenu)

            try:
                dict_of_friends[rec_token] = (friend.id, message.from_user.id, False)
                sql_add_friend_rec(message.from_user.id, rec_token)
            except:
                print ('Почему-то не добавилось в базу')




def statistics(message):
    pass
    # send_message(context, update.message.chat.id, "future update")





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




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)

