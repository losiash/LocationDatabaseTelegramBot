import sqlite3
from classes import *

conn = sqlite3.connect('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\tgbot_database.db', check_same_thread=False)
cur = conn.cursor()

def create_table():
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

def sql_add_user(chat):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (chat['id'], chat['username'], chat['first_name'], chat['last_name']))
    conn.commit()

def sql_add_location(id, time, ln , lt):
    cur.execute("INSERT INTO location_database VALUES(?, ?, ?, ?);", (id, time, ln ,lt))
    conn.commit()

def sql_add_friend_send(id1, ver_code):
    global dict_of_friends

    dict_of_friends[ver_code]=(id1, None, True)
    cur.execute("INSERT INTO friends_graph VALUES(?, ?, ?, ?);", (ver_code, id1, None, True))
    conn.commit()

def sql_add_friend_rec(id2, ver_code):
    global dict_of_friends

    dict_of_friends[ver_code]=(dict_of_friends[ver_code][0],id2,False)
    cur.execute(f"UPDATE friends_graph SET userid_receiver = {id2}  WHERE verification_code = {ver_code};")
    cur.execute(f"UPDATE friends_graph SET  active = {False}  WHERE verification_code = {ver_code};")
    conn.commit()


def loading_from_database():

    create_table()

    dict_of_friends = {}  # словарь вида -  айди пользователя - массив айди его друзей
    users = {}

    # USERS
    cur.execute("SELECT * FROM users;")
    old_users = cur.fetchall()
    mask=('id', 'username', 'first_name', 'last_name')

    for usr in old_users:
        user=new_user({mask[0]:usr[0], mask[1]:usr[1], mask[2]:usr[2], mask[3]:usr[3]})
        users[user.id]=user

    print(users, "old users")

    # GRAPH_OF_FRIENDS

    cur.execute("SELECT * FROM friends_graph")
    table = cur.fetchall()

    for agreement in table:
        dict_of_friends[agreement[0]]=(agreement[1],agreement[2],agreement[3])

    print(dict_of_friends, "old friends")

    # LOCATION_DATABASE

    return users, dict_of_friends