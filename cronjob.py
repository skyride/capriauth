import datetime

from db import getSession
from models import Api
from api import updateApiKey, apiLog

# Hook us up to the database
session = getSession()

# Update all Apis that haven't been done within the last 2 hrs
for api in session.query(Api).filter(Api.lastUpdated < (datetime.datetime.now() - datetime.timedelta(0, 1))):
    apiLog("Updating Api ID=%d..." % api.id)
    updateApiKey(api=api)
