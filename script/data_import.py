import json
import datetime

# now datetime
def now_in_jst():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    return datetime.datetime.now(jst).isoformat(timespec='seconds')

# read json
with open('./data/now.json') as rf:
    df = json.load(rf)

# update json
df.update(now=now_in_jst())

# write json
with open('./data/now.json', mode='w') as wf:
    wf.write(json.dumps(df))