import os
import sys
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement, Requirement
import requests
import datetime
from config import Config

f = file('codes.cfg')
cfg = Config(f)

AWS_ACCESS_KEY_ID = cfg.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = cfg.AWS_SECRET_ACCESS_KEY

API_KEY = cfg.API_KEY

IGNORE_LIST = ["A3PBQIXPEP19WL"]

if cfg.DEV_PROD == 1:
    print "PROD"
    HOST = 'mechanicalturk.amazonaws.com'
    QUAL = '3R5PEB0CKOM2DLVFJW0IK79PLLFO96'
else:
    HOST = 'mechanicalturk.sandbox.amazonaws.com'
    QUAL = '3ZNBPLV0N92Q4CDD8ICDTG5RJLD2CJ'

connection = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             host=HOST,
                             debug=1)

def create_hit(url=None, title=None, description=None, keywords=None, reward_amount=None, max_assignments=None, duration_in_minutes=None, lifetime_in_minutes=None, approval_delay_in_days=None, qualification_list=None):
    url = url or "https://squadtest.herokuapp.com/"
    time = datetime.datetime.utcnow().strftime("%b %d %H:%M:%S")
    title = title or "[URGENT] Compare ~45 sets of 2 Instagram posts to guess which performed better (<2 minutes)"
    description = description or "This HIT will take less than 2 minutes. Message us with any issues. Date: %s" %(time)
    keywords = keywords or ["easy", "survey", "study", "bonus", "image", "images", "compare", "comparisons", "collection", "data", "research", "listings", "simple", "photo", "answer", "opinion", "question"]
    frame_height = 800
    reward_amount = reward_amount or .25
    max_assignments = max_assignments or 67

    duration_in_minutes = duration_in_minutes or 15
    duration = datetime.timedelta(minutes=duration_in_minutes)

    lifetime_in_minutes = lifetime_in_minutes or 500
    lifetime = datetime.timedelta(minutes=lifetime_in_minutes)

    approval_delay_in_days = approval_delay_in_days or 1
    approval_delay = datetime.timedelta(days=approval_delay_in_days)

    q1 = PercentAssignmentsApprovedRequirement('GreaterThan', 95)
    q2 = NumberHitsApprovedRequirement('GreaterThan', 500)
    qualification_list = qualification_list or [q1, q2]
    qualifications = Qualifications(qualification_list)

    questionform = ExternalQuestion(url, frame_height)
    return connection.create_hit(
        title=title,
        description=description,
        keywords=keywords,
        max_assignments=max_assignments,
        question=questionform,
        reward=Price(amount=reward_amount),
        response_groups=('Minimal', 'HITDetail', 'HITQuestion', 'HITAssignmentSummary'),
        lifetime=lifetime,
        duration=duration, 
        approval_delay=approval_delay,
        qualifications=qualifications
    )

def send_workers_message(worker_ids, subject, message_text):
    for worker_id in worker_ids:
        response = connection.notify_workers(worker_id, subject, message_text)
        if response != []:
            print response

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

def make_hit_from_post(user_id, post_id):
    res = create_queue(user_id, post_id)
    queue_id = res['id']
    qual1 = Requirement(QUAL, 'GreaterThan', 0)
    qual2 = Requirement(QUAL, 'DoesNotExist')
    q1 = PercentAssignmentsApprovedRequirement('GreaterThan', 95)
    q2 = NumberHitsApprovedRequirement('GreaterThan', 500)
    response1 = create_hit(url="https://squadtest.herokuapp.com/?queueId=%s" % (queue_id), reward_amount=.45, qualification_list = [qual1])
    hit_id = response1[0].HITId
    worker_ids = [x.SubjectId for x in connection.get_all_qualifications_for_qual_type(QUAL) if x.SubjectId not in IGNORE_LIST]
    send_workers_message(worker_ids, "A new Market Intelligence HIT has been posted", "A new HIT has been posted by Market Intelligence. It has HIT_ID %s. All our HITs can be found at our requester page (http://bit.ly/20vu8m5) or by searching for Market Intelligence. You are qualified to do the HIT. This HIT has a limited number of assignments and may not be available if you reach it late." % (hit_id))
    time = datetime.datetime.utcnow().strftime("%b %d %H:%M:%S")
    create_hit(url="https://squadtest.herokuapp.com/?queueId=%s" % (queue_id), description="This is a qualifying HIT. You must take 4 of these have have an average rate of 60 percent to qualify. This HIT will take less than 2 minutes. Message us with any issues. Date: %s" %(time), reward_amount=.28, qualification_list = [q1, q2, qual2])

if __name__ == '__main__':
    user_id = '4641204'
    post_id = '1157475420733625548_4641204'
    API_URL = "http://127.0.0.1:9991/api/v0/instagram/posts/comparisons/queues/"
    data = {
        'api_key': API_KEY,
        'user_id': user_id,
        'post_id': post_id
    }
    res = requests.post(API_URL, data=data)
    print res.json()
    print len(res.json())
    if res.status_code != 200:
        print "POST Error ", res.text, data

    