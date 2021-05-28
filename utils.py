import json, os
import os.path, time, datetime

months = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
    }

def write_file(filename, data):
    path = "data/" + filename
    with open(path, 'w') as file:
        file.truncate(0)
        json.dump(data, file)
        file.close()

def read_file(filename):
    path = "data/" + filename
    try:
        with open(path, 'r') as file:
            try:
                content = json.load(file)
            except ValueError:
                content = []
    except IOError as e:
        return []
    file.close()
    return content

LIFE_TIME = 365 #days
def check_file_age(path):
    if os.path.exists(path):
        c = time.ctime(os.path.getctime(path))
        day = c[8:10]
        month = months[c[4:7]]
        year = c[-4:]

        file_date = datetime.datetime(int(year), int(month), int(day))
        now = datetime.datetime.now()
        difference = file_date - now

        if abs(difference.days) > LIFE_TIME:
            os.remove(path)