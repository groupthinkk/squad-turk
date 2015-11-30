from boto.mturk.connection import MTurkConnection
import requests
from config import Config

f = file('codes.cfg')
cfg = Config(f)

AWS_ACCESS_KEY_ID = cfg.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = cfg.AWS_SECRET_ACCESS_KEY

API_KEY = cfg.API_KEY

if cfg.DEV_PROD == 1:
    print "PROD"
    HOST = 'mechanicalturk.amazonaws.com'
    QUAL = '3R5PEB0CKOM2DLVFJW0IK79PLLFO96'
else:
    HOST = 'mechanicalturk.sandbox.amazonaws.com'
    QUAL = '3ZNBPLV0N92Q4CDD8ICDTG5RJLD2CJ'

def get_all_reviewable_hits(mtc):
    page_size = 50
    hits = mtc.get_reviewable_hits(page_size=page_size)
    print "Total results to fetch %s " % hits.TotalNumResults
    print "Request hits page %i" % 1
    total_pages = float(hits.TotalNumResults)/page_size
    int_total= int(total_pages)
    if(total_pages-int_total>0):
        total_pages = int_total+1
    else:
        total_pages = int_total
    pn = 1
    while pn < total_pages:
        pn = pn + 1
        print "Request hits page %i" % pn
        temp_hits = mtc.get_reviewable_hits(page_size=page_size,page_number=pn)
        hits.extend(temp_hits)
    return hits

mtc = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      host=HOST)

hits = get_all_reviewable_hits(mtc)

for hit in hits:
    assignments = mtc.get_assignments(hit.HITId)
    for assignment in assignments:
        if assignment.AssignmentStatus == "Submitted":
            mtc.approve_assignment(assignment.AssignmentId)
        else:
            print assignment.AssignmentStatus
