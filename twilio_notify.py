from twilio.rest import TwilioRestClient
from pymongo import MongoClient
from config import Config
import requests

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
    API_URL = "http://squadapi.com/api/v0/instagram/posts/comparisons/queues/"
    data = {
        'api_key': API_KEY,
        'user_id': user_id,
        'post_id': post_id
    }
    res = requests.post(API_URL, data=data)
    if res.status_code != 200:
        print "POST Error ", res.text, data
    return res.json()

def send_texts_from_post(user_id, post_id):
    res = create_queue(user_id, post_id)
    queue_id = res['id']
    user_data = db['users'].find(None, {'phone_number': 1} )
    for user in user_data:
        phone_number = user['phone_number']
        try:
            client.messages.create(to=phone_number, from_="+19292947687", body="Hey there! Here is your next challenge! Play ASAP for more points: http://squadtest.heroku.com/q/%d" % queue_id)
        except Exception, e:
            print phone_number, e