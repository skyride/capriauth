from datetime import datetime

from db import *
from models import *
from api import addApi, updateApiKey, calculateTags

# Hook us up to the DB
auth = getSession(echo=True)

# Test add a user
#ed_user = User(username='skyride', password='asd', email='skylinerspeeder@gmail.com', registeredOn=datetime.utcnow(), active=True)
#auth.add(ed_user)
#auth.commit()
#print ed_user.id


# Query users
#for x in auth.query(User).order_by(User.id).filter(User.username == "skyride"):
#	print x.logins

# Query for API
#for x in auth.query(Api):
#	print x

# Query for Character
#for x in auth.query(Character):
#	print x

# Query for Alliance
#for x in auth.query(Alliance):
#	print x.corporations

# Query for Corporation
#for x in auth.query(Corporation):
#	print x

# Query for InvType
#for x in auth.query(InvType).filter(InvType.typeID == 34):
#	print x.marketGroup

# Query for InvCategory
#for x in auth.query(InvCategory).filter(InvCategory.categoryID == 18):
#	print x

# Query for InvGroups
#for x in auth.query(InvGroup).filter(InvGroup.groupID == 46):
#	print x.types

# Query for InvMarketGroup
#for x in auth.query(InvMarketGroup).filter(InvMarketGroup.marketGroupID == 81):
#	print x.types

# Query for Skill
#for x in auth.query(Skill):
#	print x

# Query for Asset
#for x in auth.query(Asset):
#	print x

# Test API Checking
#for x in auth.query(Api):
#	updateApiKey(x)

# Test adding an API key
#user = auth.query(User).filter(User.username == "skyride").first()
#print addApi(user=user, name="skyride275", keyID=123456, vCode="asdasd")

# Test join
#for x in auth.query(Asset, InvGroup.groupName).join(InvType).join(InvGroup).join(Character).join(Api)\
#        .filter(InvGroup.categoryID == 6,\
#                Api.userId == 7).group_by(InvGroup.groupID).all():
#    print x.groupName

# Test the tag calculation
#calculateTags(auth.query(User).filter(User.id == 7).first())

# Query for JumpClone
#for x in auth.query(JumpClone):
#    print x

# Query for Implants
for x in auth.query(Implant):
    print x
