import datetime

from db import getSession
from models import Api, User
from api import updateApiKey, apiLog, calculateTags

# Hook us up to the database
session = getSession()

# Update all Apis that haven't been done within the last 2 hrs
for user in session.query(User).join(Api).filter(Api.lastUpdated < (datetime.datetime.now() - datetime.timedelta(0, 1))).group_by(User.id).all():
    for api in user.apis:
        if api.lastUpdated < (datetime.datetime.now() - datetime.timedelta(0, 1)):
            apiLog("Updating Api ID=%d..." % api.id)
            updateApiKey(api=api, session=session)
    apiLog("Recalculating tags for User ID=%d..." % user.id)
    calculateTags(user)
