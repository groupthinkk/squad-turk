import os
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement, Requirement
import requests
import datetime

f = file('codes.cfg')
cfg = Config(f)

AWS_ACCESS_KEY_ID = cfg.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = cfg.AWS_SECRET_ACCESS_KEY

API_KEY = cfg.API_KEY

if cfg.DEV_PROD == 1:
    print "PROD"
    #HOST = 'mechanicalturk.amazonaws.com'
    #QUAL = '3R5PEB0CKOM2DLVFJW0IK79PLLFO96'
else:
    HOST = 'mechanicalturk.sandbox.amazonaws.com'
    QUAL = '3ZNBPLV0N92Q4CDD8ICDTG5RJLD2CJ'

connection = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             host=HOST,
                             debug=1)

def update_ratings(qualification_name):
    qualification_type_id = connection.search_qualification_types(qualification_name)[0].QualificationTypeId
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
    print results
    for r in results:
        turk_id = r['turker']['turker_id']
        rating = int(r['correctness']*100)
        if rating >= 60:
            try:
                connection.assign_qualification(qualification_type_id, turk_id, value=rating, send_notification=True)
                print "Assigned"
            except:
                try:
                    connection.update_qualification_score(qualification_type_id, turk_id, value=rating)
                    print "Updated"
                except:
                    print "%s was not found" % (turk_id)
        else:
            try:
                connection.revoke_qualification(turk_id, qualification_type_id, reason="You fell below the required response percentage.")
                print "Removed"
            except:
                print "%s was never qualified" % (turk_id)

if __name__ == '__main__':
    update_ratings("squad_rating")


