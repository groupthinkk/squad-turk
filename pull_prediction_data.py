import os
import sys
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement, Requirement
import requests
import datetime
from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError
import csv
from config import Config

f = file('codes.cfg')
cfg = Config(f)

AWS_ACCESS_KEY_ID = cfg.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = cfg.AWS_SECRET_ACCESS_KEY

API_KEY = cfg.API_KEY

if True:
    print "PROD"
    HOST = 'mechanicalturk.amazonaws.com'
else:
    HOST = 'mechanicalturk.sandbox.amazonaws.com'

connection = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             host=HOST,
                             debug=1)

client_id = "375701af44384b6da4230f343a528b92"
client_secret = "9620d4aef36f4e5b9139731497babcdb"

api = InstagramAPI(client_id=client_id, client_secret=client_secret)

def make_prediction_csv():
    hits = list(connection.get_all_hits())
    API_URL = "http://squadapi.com/api/v0/predictions/instagram/posts?api_key=" + API_KEY
    _next = API_URL
    results = []
    while (_next):
        res = requests.get(_next)
        if res.status_code != 200:
            print "POST Error ", res.text, _next
            return
        j = res.json()
        results.extend(j['results'])
        _next = j['next']
    csvfile = open("predictions-%s.csv" % (datetime.datetime.strftime(datetime.datetime.utcnow(), '%m-%d-%y|%H-%M')), "wb")
    fieldnames = [
                    'hit_id', 
                    'new_post', 
                    'prediction_lower_bound', 
                    'prediction_upper_bound', 
                    'like_count_at_last_prediction', 
                    'like_count_at_export',
                    'post_created_time',
                    'hit_created_time',
                    'hit_updated_time',
                    'export_time',
                    'expert_hit'
                ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for post in results:
        row = {}
        row['hit_id'] = post['hit_id']
        row['new_post'] = post['post']['post_id']
        row['prediction_lower_bound'] = post['lower_bound']
        row['prediction_upper_bound'] = post['upper_bound']
        row['like_count_at_last_prediction'] = post['post']['likes_count']
        try:
            row['like_count_at_export'] = api.media(post['post']['post_id']).like_count
        except InstagramAPIError:
            row['like_count_at_export'] = 'NOT FOUND'
        row['post_created_time'] = datetime.datetime.strptime(post['post']['created_datetime'], "%Y-%m-%dT%H:%M:%SZ")
        row['hit_created_time'] = datetime.datetime.strptime(post['created_datetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
        row['hit_updated_time'] = datetime.datetime.strptime(post['updated_datetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
        row['export_time'] = datetime.datetime.utcnow()
        row['expert_hit'] = ''
        for hit in hits:
            if (row['hit_id'] == hit.HITId):
                if float(hit.Amount) == .45:
                    row['expert_hit'] = '1'
                break
        writer.writerow(row)

def make_predictor_csv():
    API_URL = "http://squadapi.com/api/v0/predictions/turkers/performance" + "?api_key=" + API_KEY
    data = {"api_key":API_KEY}
    _next = API_URL
    results = []
    while (_next):
        res = requests.get(_next)
        if res.status_code != 200:
            print "POST Error ", res.text, data, _next
            return
        j = res.json()
        results.extend(j['results'])
        _next = j['next']
    csvfile = open("predictors-%s.csv" % (datetime.datetime.strftime(datetime.datetime.utcnow(), '%m-%d-%y|%H-%M')), "wb")
    fieldnames = [
                    'turk_id',
                    'rating'
                ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for post in results:
        turk_id = post['turker']['turker_id']
        rating = post['correctness']*100
        if rating >= 59.5:
            writer.writerow({'turk_id':turk_id, 'rating':rating})
        else:
            break

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == '0':
        make_prediction_csv()
    else:
        make_predictor_csv()
