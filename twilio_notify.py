from twilio.rest import TwilioRestClient
from pymongo import MongoClient
from config import Config
import requests
from random import shuffle
from datetime import datetime, timedelta
import sys

account_sid = "AC92676a683900b40e7ba19d1b9a78a5ef"
auth_token = "4de6b64136ddfcf839562af528f9304e"
client = TwilioRestClient(account_sid, auth_token)
 
db_client = MongoClient("ds037713-a0.mongolab.com", 37713)
db = db_client["turksquad"]
db.authenticate("sweyn", "sweynsquad")

f = file('codes.cfg')
cfg = Config(f)

API_KEY = cfg.API_KEY

def create_queue(user_id, post_id):
    #API_URL = "http://squadapi.com/api/v0/instagram/posts/comparisons/queues/"
    API_URL = "http://localhost:9991/api/v0/instagram/posts/comparisons/queues/"
    data = {
        'api_key': API_KEY,
        'user_id': user_id,
        'post_id': post_id
    }
    res = requests.post(API_URL, data=data)
    if res.status_code != 200:
        print "POST Error ", res.text, data
    return res.json()

def send_text(mes):
    user_data = list(db['users'].find(None, {'phone_number': 1} ))
    for i in xrange(len(user_data)):
        phone_number = user_data[i]['phone_number']
        try:
            client.messages.create(to=phone_number, from_="+19292947687", body=mes)
        except Exception, e:
            print phone_number, e

def send_texts_from_post(user_id, post_id):
    user_data = list(db['users'].find(None, {'phone_number': 1} ))
    all_queues = create_queue(user_id, post_id)
    for i in xrange(len(user_data)):
        phone_number = user_data[i]['phone_number']
        #queue_id = all_queues[i % len(all_queues)]['id']
        queue_id = all_queues['id']
        try:
            client.messages.create(to=phone_number, from_="+19292947687", body="Squad: Hey there! Here is your next challenge! Play ASAP for more points: http://squadtest.heroku.com/q/%d" % queue_id)
        except Exception, e:
            print phone_number, e

def send_texts_from_post_noqueue():
    now = datetime.now()
    user_data = list(db['users'].find(None, {'phone_number': 1, 'last_queue': 1} ))
    for i in xrange(len(user_data)):
        phone_number = user_data[i]['phone_number']
        if now - user_data[i]['last_queue'] > timedelta(days=2):
        #queue_id = all_queues[i % len(all_queues)]['id']
        #queue_id = all_queues['id']
            try:
                client.messages.create(to=phone_number, from_="+19292947687", body="Squad: You're falling in the leaderboard over the last 2 days! Play now to stay ahead! http://goo.gl/Mt1Wa0")   
                db['users'].update({'phone_number': phone_number}, {"$set": {"last_queue": datetime.now() - timedelta(hours = 1)}})
            except Exception, e:
                print phone_number, e
    # queue_type_list = ['food', 'fashion', 'sports']
    # shuffle(queue_type_list)
    # db['users'].update(
    #     {},
    #     {"$set": {"available_queues": queue_type_list} },
    #     multi=True
    # )

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "0":
        send_text("Squad: Good news! You now have unlimited queues! Log in any time to do a queue based on a specific Instagram account of your choice. Which will you master? http://goo.gl/Mt1Wa0")
    else:
        send_texts_from_post_noqueue()
