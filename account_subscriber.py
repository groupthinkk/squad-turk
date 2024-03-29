from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError
from pymongo import MongoClient
import gevent
import sys
import make_hit

import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()

NUM_POSTS_TO_HIT = 0

client_id = "d178391dddfa4e6cb79bc1226a3e11a7"
client_secret = "98642c73a1ed46e8bf29f4682c728681"

api = InstagramAPI(client_id=client_id, client_secret=client_secret)

client = MongoClient()
db = client['SQUAD']

def add_tracked_user(username):
    if db['tracked_users'].find_one({"username": username}) != None:
        return False
    while(1):
        datalist = api.user_search(username, 100)
        break
    for data in datalist:
        if data.username == username:
            if get_user_posts(str(data.id), []) != False:
                db['tracked_users'].insert({'username': username,'user_id':str(data.id), 'post_since_last_hit':1})
                return True
            else:
                return False
    return False

def remove_tracked_user(username):
    return True if db['tracked_users'].remove({"username": username}) else False

def get_tracked_users():
    q = db['tracked_users'].find()
    return [entry['username'] for entry in q]

def get_user_posts(user_id, append_list):
    try:
        ret = api.user_recent_media(user_id=user_id, count=1)
    except InstagramAPIError as e:
        if (int(e.status_code) == 400):
            return False
    append_list.append(ret[0])
    return True

def do_pull():
    new_last_posts = []
    last_posts_q = db['last_posts'].find_one()
    if last_posts_q:
        last_posts = last_posts_q['last_posts']
    else:
        last_posts = False
    q = db['tracked_users'].find()
    post_data_list = []
    requests = []
    for entry in q:
        requests.append(gevent.spawn(get_user_posts, entry['user_id'], post_data_list))
    gevent.joinall(requests)
    for posts in post_data_list:
        if not last_posts or posts[0].id not in last_posts:
            #-----------MAKE_HIT()-----------
            if db['tracked_users'].find_one({'user_id': posts[0].user.id})['post_since_last_hit'] >= NUM_POSTS_TO_HIT:
                db['tracked_users'].update_one({'user_id': posts[0].user.id}, {'$set': {'post_since_last_hit': 1}})
                make_hit.make_hit_from_post(posts[0].user.id, posts[0].id)
                print "Made HIT from %s" % (posts[0].id)
            else:
                db['tracked_users'].update_one({'user_id': posts[0].user.id}, {'$inc': {'post_since_last_hit': 1}})
            #--------------------------------
        new_last_posts.append(posts[0].id)
    if last_posts:
        db['last_posts'].replace_one({'last_posts':last_posts}, {'last_posts':new_last_posts})
    else:
        db['last_posts'].insert({'last_posts':new_last_posts})

def populate_last_posts():
    q = db['tracked_users'].find()
    new_last_posts = []
    last_posts_q = db['last_posts'].find_one()
    if last_posts_q:
        last_posts = last_posts_q['last_posts']
    else:
        last_posts = False
    post_data_list = []
    requests = []
    for entry in q:
        requests.append(gevent.spawn(get_user_posts, entry['user_id'], post_data_list))
    gevent.joinall(requests)
    for posts in post_data_list:
        new_last_posts.append(posts[0].id)
    if last_posts:
        db['last_posts'].replace_one({'last_posts':last_posts}, {'last_posts':new_last_posts})
    else:
        db['last_posts'].insert({'last_posts':new_last_posts})

if __name__ == '__main__':
    print "Running"
    if len(sys.argv) > 1:
        if sys.argv[1] == '0':
            populate_last_posts()
        elif sys.argv[1] == '1':
            add_tracked_user(sys.argv[2])
        elif sys.argv[1] == '2':
            remove_tracked_user(sys.argv[2])
        elif sys.argv[1] == '3':
            print get_tracked_users()
    else:
        do_pull()
