from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError
from pymongo import MongoClient
import gevent
import make_hit

import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()

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
            if get_user_posts(str(data.id)) != False:
                db['tracked_users'].insert({'username': username,'user_id':str(data.id)})
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
            make_hit.make_hit_from_post(posts[0].user, posts[0].id)
            #--------------------------------
        new_last_posts.append(posts[0].id)
    if last_posts:
        db['last_posts'].replace_one({'last_posts':last_posts}, {'last_posts':new_last_posts})
    else:
        db['last_posts'].insert({'last_posts':new_last_posts})

if __name__ == '__main__':
    do_pull()
