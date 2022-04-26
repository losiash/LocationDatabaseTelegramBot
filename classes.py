import time
import datetime

class new_point:
    def __init__(self, update, user_send):
        message = update.edited_message or update.message
        location = message.location
        self.name = None
        self.current_pos = (location.latitude, location.longitude)
        self.horizontal_accuracy = None or location.horizontal_accuracy
        self.heading = None or location.heading
        self.time_stamp = message.forward_date or message.edit_date or message.date
        self.message_date = message.date
        self.user = user_send
        # self.user = users.get(message.chat.id) or new_user(message.chat)  #????
        self.kod = (self.user.id, message.message_id)
        self.live_period = None or location.live_period
        self.user.current_location = self
        print (self)

    def __str__(self):
        return  f'{self.time_stamp}, {self.name}, {self.kod}, {self.current_pos}, {self.horizontal_accuracy}, {self.heading}'



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
        self.username = chat['username']
        self.current_location = None
        self.id = chat['id']
        self.first_name = chat['first_name']
        self.last_name = chat['last_name']
        self.points = {}
        self.points_seconds = {}
        self.tracks = {}
        print (f' пользователь: ', self)





    def __str__(self):
        return f'user_id: {self.id},  username: {self.username}, first_name: {self.first_name}, last_name: {self.last_name}'