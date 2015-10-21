import os
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement

import datetime

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

if os.environ.get("DEV_PROD"):
    HOST = 'mechanicalturk.amazonaws.com'
else:
    HOST = 'mechanicalturk.sandbox.amazonaws.com'

connection = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             host=HOST,
                             debug=1)

def create_hit(url=None, title=None, description=None, keywords=None, reward_amount=None, max_assignments=None, duration_in_minutes=None, lifetime_in_minutes=None, approval_delay_in_days=None, qualification_list=None):
    url = url or "https://squadtest.herokuapp.com/"
    title = title or "[URGENT] Compare 20 sets of 2 Instagram posts to guess which performed better (<2 minutes)"
    description = description or "This HIT must be completed within 15 minutes of it being posted. It will take less than 2 minutes."
    keywords = keywords or ["easy", "survey", "study", "bonus", "image", "images", "compare", "comparisons", "collection", "data", "research", "listings", "simple", "photo", "answer", "opinion", "question"]
    frame_height = 800
    reward_amount = reward_amount or .25
    max_assignments = max_assignments or 30

    duration_in_minutes = duration_in_minutes or 10
    duration = datetime.timedelta(minutes=duration_in_minutes)

    lifetime_in_minutes = lifetime_in_minutes or 15
    lifetime = datetime.timedelta(minutes=lifetime_in_minutes)

    approval_delay_in_days = approval_delay_in_days or 5
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

def make_hit_from_post(post_id):
    queue_id = POST_TO_API(post_id)
    response = create_hit(url="https://squadtest.herokuapp.com/?queueId=%s" % (queue_id))
    hit_id = response[0].HITId
    worker_ids = [x.SubjectId for x in connection.get_all_qualifications_for_qual_type("3R5PEB0CKOM2DLVFJW0IK79PLLFO96")]
    send_workers_message(worker_ids, "[URGENT: 15 minutes to complete] A new Market Intelligence HIT has been posted", "A new HIT has been posted by Market Intelligence. It has HIT_ID %s. You are qualified to do the HIT. You have 15 minutes to complete the HIT." % (hit_id))