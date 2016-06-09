from sqlalchemy.sql import func
from models import *

def getShipContents(session, itemID):
	contents = []
	prevgroup = -1
	group = None

	for x in session.query(Asset, InvType, InvGroup, func.sum(Asset.quantity).label("quantity")).join(InvType).join(InvGroup).filter(Asset.locationID == itemID).group_by(InvType.groupID, InvType.typeID).order_by(InvType.groupID).all():
		if x != None:
			if x.InvGroup.groupID != prevgroup:
				if group != None:
					contents.append(group)
				group = {"group": x.InvGroup, "items": [] }
			group['items'].append(x)
			prevgroup = x.InvGroup.groupID
	contents.append(group)
	return contents
