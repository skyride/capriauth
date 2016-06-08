from sqlalchemy.sql import func
from models import *

# Represents a ship for the purpose of getting info
class Ship():
	session = None
	asset = None
	invType = None
	invGroup = None
	character = None
	attributes = None
	contents = None		# Content is an array containing tuples of Assets, invType and invGroup objects

	def __init__(self, session, ship, contents, character):
		self.session = session
		self.asset = ship.Asset
		self.invType = ship.InvType
		self.invGroup = ship.InvGroup
		self.contents = contents
		self.character = character

	def countHighSlots(self):
		self.getAttributes()
		for x in self.attributes:
			if x.attributeID == 14:
				return int(x.value())

	def countMidSlots(self):
		self.getAttributes()
		for x in self.attributes:
			if x.attributeID == 13:
				return int(x.value())

	def countLowSlots(self):
		self.getAttributes()
		for x in self.attributes:
			if x.attributeID == 12:
				return int(x.value())

	def countRigSlots(self):
		self.getAttributes()
		for x in self.attributes:
			if x.attributeID == 1137:
				return int(x.value())

	def countSubSlots(self):
		if self.invType.groupID == 963:
			return 5
		else:
			return 0


	# Returns the high slots
	def getHighMod(self, position):
		position = position + (27-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID != 8:
					return x


	def getHighCharge(self, position):
		position = position + (27-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID == 8:
					return x

	# Returns the mid slots
	def getMidMod(self, position):
		position = position + (19-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID != 8:
					return x


	def getMidCharge(self, position):
		position = position + (19-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID == 8:
					return x

	# Returns the low slots
	def getLowMod(self, position):
		position = position + (11-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID != 8:
					return x


	def getLowCharge(self, position):
		position = position + (11-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID == 8:
					return x

	# Returns the Rigs
	def getRig(self, position):
		position = position + (92-1)
		for x in self.contents:
			if x.Asset.flag == position:
				# Check if its a charge
				if x.InvGroup.categoryID != 8:
					return x



	def getContentsByGroup(self):
		contents = []
		prevgroup = -1
		group = None

		for x in self.session.query(Asset, InvType, InvGroup, func.sum(Asset.quantity).label("quantity")).join(InvType).join(InvGroup).filter(Asset.locationID == self.asset.itemID).group_by(InvType.groupID, InvType.typeID).order_by(InvType.groupID).order_by(InvType.typeID).all():
			if x != None:
				if x.InvGroup.groupID != prevgroup:
					if group != None:
						contents.append(group)
					group = {"group": x.InvGroup, "items": [] }
				group['items'].append(x)
				prevgroup = x.InvGroup.groupID
		contents.append(group)
		return contents

	def getAttributes(self):
		if self.attributes == None:
			self.attributes = self.invType.attributes



# Builds and returns a ship object
def getShip(session, itemID):
	ship = session.query(Asset, InvType, InvGroup).join(InvType).join(InvGroup).join(Character).filter(Asset.itemID == itemID).first()
	if ship == None:
		return None
	contents = session.query(Asset, InvType, InvGroup, Asset.quantity).join(InvType).join(InvGroup).filter(Asset.locationID == itemID).order_by(InvType.groupID).all()
	character = ship.Asset.character
	ship = Ship(session, ship, contents, character)
	return ship
