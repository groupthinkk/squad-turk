from config import Config
import requests

f = file('codes.cfg')
cfg = Config(f)

AWS_ACCESS_KEY_ID = cfg.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = cfg.AWS_SECRET_ACCESS_KEY

API_KEY = cfg.API_KEY

API_URL = "http://squadapi.com/api/v0/predictions/hits?api_key=" + API_KEY
_next = API_URL
results = []
while (_next):
    res = requests.get(_next)
    if res.status_code != 200:
        print "POST Error ", res.text, _next
        break
    j = res.json()
    for entry in j['results']:
        if entry['turker']['turker_id'] == 'A2LQ33BQ8G259D':
            print entry['hit_id']
            break
    _next = j['next']


