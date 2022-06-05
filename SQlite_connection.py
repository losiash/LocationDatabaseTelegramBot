import sqlite3
from classes import *

conn = sqlite3.connect(r'telegram_bot_database.db', check_same_thread=False)
path = ''
cur = conn.cursor()

dict_of_friends = {}  # словарь вида -  айди пользователя - массив айди его друзей
users = {}
location_coords = {}


def create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
       userid INT PRIMARY KEY,
       username TEXT,
       first_name TEXT,
       second_name TEXT);
    """)

    cur.execute("""CREATE TABLE IF NOT EXISTS friends_graph(
       verification_code TEXT PRIMARY KEY,
       userid_sender INT,
       userid_receiver INT,
       active BOOLEAN);
    """)

    cur.execute("""CREATE TABLE IF NOT EXISTS location_database(
       lat FLOAT,
       lon FLOAT,
       name TEXT,
       user_id INT,
       message_id INT,
       time_stamp TEXT,
       message_date TEXT
       );
    """)

    conn.commit()


def sql_add_user(message_dict):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (message_dict['id'], message_dict['username'],
                                                          message_dict['first_name'], message_dict['last_name']))
    conn.commit()


def sql_add_location(lt, ln, user_id=None, message_id=None, name=None, time_stamp=None, message_date=None):
    cur.execute('SELECT * FROM location_database WHERE (lat = ?) AND (lon = ?)', (lt, ln))

    if cur.fetchall():
        cur.execute("UPDATE location_database SET name = ?  WHERE (lat = ?) AND (lon = ?);", (name, lt, ln))
    else:
        cur.execute("INSERT INTO location_database VALUES(?, ?, ?, ?, ?, ?, ?);",
                    (lt, ln, name, user_id, message_id, time_stamp, message_date))
    conn.commit()


def sql_add_friend_send(id1, ver_code):
    global dict_of_friends
    cur.execute("INSERT INTO friends_graph VALUES(?, ?, ?, ?);", (ver_code, id1, None, True))
    conn.commit()


def sql_add_friend_rec(id2, ver_code):
    global dict_of_friends
    cur.execute(f"UPDATE friends_graph SET userid_receiver = ?  WHERE verification_code = ?;", (id2, ver_code))
    cur.execute(f"UPDATE friends_graph SET  active = ?  WHERE verification_code = ?;", (False, ver_code))
    conn.commit()


def loading_from_database():
    create_table()

    # USERS
    cur.execute("SELECT * FROM users;")
    old_users = cur.fetchall()
    mask = ('id', 'username', 'first_name', 'last_name')

    for usr in old_users:
        user = NewUser({mask[0]: usr[0], mask[1]: usr[1], mask[2]: usr[2], mask[3]: usr[3]})
        users[user.id] = user

    print(users, "old users")

    # GRAPH_OF_FRIENDS
    cur.execute("SELECT * FROM friends_graph")
    table = cur.fetchall()

    for agreement in table:
        dict_of_friends[agreement[0]] = (agreement[1], agreement[2], agreement[3])

    print(dict_of_friends, "old friends")

    # SET_POINTS
    with open(path + "set_of_points.txt", "r", encoding='utf-8') as f:
        for line in f.readlines():
            name, lat, lon = line.split("\t")
            sql_add_location(lat, lon, name=name)

    # LOCATION_DATABASE
    cur.execute("SELECT * FROM location_database")
    table_coord = cur.fetchall()

    for agreement in table_coord:
        location_coords[(agreement[0], agreement[1])] = (
        agreement[2], agreement[3], agreement[4], agreement[5], agreement[6])

    print(location_coords, "------------------------------------------------------------------------------------")
    return users, dict_of_friends, location_coords
