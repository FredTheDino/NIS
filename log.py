import datetime

def log(message):
    stamp = get_time_stamp()
    print(stamp)
    print(message)

    f = open("log.txt", "w")
    f.write(stamp)
    f.write("\n")
    f.write(message)
    f.write("\n")
    f.flush()
    f.close()

def get_time_stamp():
    now = datetime.datetime.now()
    return "[{0:0>2}:{1:0>2}]".format(now.hour, now.minute)

# Try to refactor this better...
# Then we can look at improvements.
