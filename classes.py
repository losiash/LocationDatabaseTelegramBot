import time
import datetime


class NewPoint:
    def __init__(self, message, user_send):
        location = message.location
        self.name = None
        self.current_pos = (location.latitude, location.longitude)
        self.horizontal_accuracy = None or location.horizontal_accuracy
        self.heading = None or location.heading
        self.time_stamp = message.forward_date or message.edit_date or message.date
        self.message_date = message.date
        self.user = user_send
        self.kod = (self.user.id, message.message_id)
        self.live_period = None or location.live_period
        self.user.current_location = self
        print (self)

    def __str__(self):
        return  f'{self.time_stamp}, {self.name}, {self.kod}, {self.current_pos}, {self.horizontal_accuracy}, {self.heading}'


class NewTrack:
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


class NewUser:
    def __init__(self, message_dict):
        self.username = message_dict['username']
        self.current_location = None
        self.id = message_dict['id']
        self.first_name = message_dict['first_name']
        self.last_name = message_dict['last_name']
        self.points = {}
        self.points_seconds = {}
        self.tracks = {}
        print (f' пользователь: ', self)

    def __str__(self):
        return f'user_id: {self.id},  username: {self.username}, first_name: {self.first_name}, last_name: {self.last_name}'