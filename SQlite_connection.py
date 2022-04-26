import sqlite3
from classes import *

conn = sqlite3.connect('C:\\Users\\David\\Documents\\itmo_university\\informatics\\logs\\tgbot_database.db', check_same_thread=False)
cur = conn.cursor()

temp_mas=[("Проспект Ветеранов",59.84188,30.251543
),("Ленинский проспект",59.851677,30.268279
),("Автово",59.867369,30.261345
),("Кировский завод",59.879726,30.261908
),("Нарвская",59.901169,30.274676
),("Балтийская",59.907245,30.299217
),("Технологический институт-1",59.916799,30.318967
),("Пушкинская",59.920757,30.329641
),("Владимирская",59.927467,30.347875
),("Площадь Восстания",59.931483,30.36036
),("Чернышевская",59.944558,30.359754
),("Площадь Ленина",59.955725,30.355957
),("Выборгская",59.97111,30.347553
),("Лесная",59.98477,30.344201
),("Площадь Мужества",59.999655,30.366595
),("Политехническая",60.008926,30.370952
),("Академическая",60.012763,30.395706
),("Гражданский проспект",60.03481,30.418087
),("Девяткино",60.049799,30.442248
),("Купчино",59.829887,30.375399
),("Звёздная",59.833228,30.349616
),("Московская",59.852192,30.322206
),("Парк Победы",59.86659,30.321712
),("Электросила",59.879425,30.318658
),("Московские Ворота",59.891924,30.317751
),("Фрунзенская",59.906155,30.317509
),("Технологический институт-2",59.916622,30.318505
),("Сенная площадь",59.92709,30.320378
),("Невский проспект",59.935601,30.327134
),("Горьковская",59.956323,30.318724
),("Петроградская",59.966465,30.311432
),("Чёрная речка",59.985574,30.300792
),("Пионерская",60.002576,30.296791
),("Удельная",60.016707,30.315421
),("Озерки",60.037141,30.321529
),("Проспект Просвещения",60.051416,30.332632
),("Парнас",60.06715,30.334128
),("Приморская",59.948545,30.234526
),("Василеостровская",59.942927,30.278159
),("Гостиный Двор",59.934049,30.333772
),("Маяковская",59.931612,30.35491
),("Площадь Александра Невского-1",59.924314,30.385102
),("Елизаровская",59.896705,30.423637
),("Ломоносовская",59.877433,30.441951
),("Пролетарская",59.865275,30.47026
),("Обухово",59.848795,30.457805
),("Рыбацкое",59.830943,30.500455
),("Улица Дыбенко",59.907573,30.483292
),("Проспект Большевиков",59.919819,30.466908
),("Ладожская",59.93244,30.439474
),("Новочеркасская",59.92933,30.412918
),("Площадь Александра Невского-2",59.92365,30.383471
),("Лиговский проспект",59.920747,30.355245
),("Достоевская",59.928072,30.345746
),("Спасская",59.926839,30.319752
),("Международная",59.869966,30.379045
),("Бухарестская",59.883681,30.369673
),("Волковская",59.896265,30.35686
),("Обводный канал",59.914697,30.349361
),("Звенигородская",59.922304,30.335784
),("Садовая",59.927008,30.317456
),("Адмиралтейская",59.935877,30.314886
),("Спортивная-1",59.952078,30.291312
),("Спортивная-2",59.950365,30.287356
),("Чкаловская",59.961035,30.291964
),("Крестовский остров",59.971838,30.259427
),("Старая Деревня",59.989228,30.255169
),("Комендантский проспект",60.008356,30.258915
),("Балтийский вокзал",59.907723,30.29885
),("Витебский вокзал",59.920955,30.32893
),("Ладожский вокзал",59.931109,30.439826
),("Московский вокзал",59.929159,30.360055
),("Финляндский вокзал",59.955982,30.355729
),("Единый пассажирский терминал Пулково",59.799963,30.271598)]

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
       verification_code INT PRIMARY KEY,
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

    # cur.execute("""CREATE TABLE IF NOT EXISTS location_coordinates(
    #    name TEXT,
    #    longitude FLOAT,
    #    latitude FLOAT);
    # """)
    conn.commit()

def sql_add_user(chat):
    cur.execute("INSERT INTO users VALUES(?, ?, ?, ?);", (chat['id'], chat['username'], chat['first_name'], chat['last_name']))
    conn.commit()

def sql_add_location(lt , ln,  user_id=None, message_id=None, name=None, time_stamp=None, message_date=None):
    # print(ln, lt, location_coords.keys())



    cur.execute('SELECT * FROM location_database WHERE (lat = ?) AND (lon = ?)', (lt,ln))

    if cur.fetchall():
        cur.execute("UPDATE location_database SET name = ?  WHERE (lat = ?) AND (lon = ?);", (name, lt, ln))
    else:
        cur.execute("INSERT INTO location_database VALUES(?, ?, ?, ?, ?, ?, ?);", (lt, ln , name, user_id, message_id, time_stamp, message_date))
    conn.commit()


def sql_add_friend_send(id1, ver_code):
    global dict_of_friends

    dict_of_friends[ver_code]=(id1, None, True)
    cur.execute("INSERT INTO friends_graph VALUES(?, ?, ?, ?);", (ver_code, id1, None, True))
    conn.commit()

# def sql_add_new_location(name, coord):
#     cur.execute("INSERT INTO location_coordinates VALUES(?, ?, ?);", (name, coord[0], coord[1]))
#     conn.commit()

def sql_add_friend_rec(id2, ver_code):
    global dict_of_friends

    dict_of_friends[ver_code]=(dict_of_friends[ver_code][0],id2,False)
    cur.execute(f"UPDATE friends_graph SET userid_receiver = ?  WHERE verification_code = ?;", (id2,ver_code))
    cur.execute(f"UPDATE friends_graph SET  active = ?  WHERE verification_code = ?;", (False,ver_code))
    conn.commit()


def loading_from_database():

    create_table()



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


    # TEMP

    for kor in temp_mas: #в будущем поместить настраевыемые автором точки в эксель и доставать pandas
        sql_add_location(kor[1], kor[2], name=kor[0])


    cur.execute("SELECT * FROM location_database")
    table_coord = cur.fetchall()

    for agreement in table_coord:
        location_coords[(agreement[0],agreement[1])]=(agreement[2], agreement[3], agreement[4], agreement[5], agreement[6])

    print(location_coords, "------------------------------------------------------------------------------------")
    return users, dict_of_friends, location_coords


