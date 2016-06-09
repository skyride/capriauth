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

	def getContentsByLocation(self):
		contents = []
		prevgroup = -1
		group = None

		for x in self.session.query(Asset, InvType, InvGroup, InvFlag, func.sum(Asset.quantity).label("quantity")).join(InvType).join(InvGroup).join(InvFlag).filter(Asset.locationID == self.asset.itemID, sqlalchemy.not_(InvFlag.flagText.contains("slot")), sqlalchemy.not_(InvFlag.flagText.contains("tube"))).group_by(Asset.flag, Asset.typeID).order_by(Asset.flag).order_by(InvType.groupID).all():
			if x != None:
				if x.InvFlag.flagID != prevgroup:
					if group != None:
						contents.append(group)
					group = {"flag": x.InvFlag, "items": [] }
				group['items'].append(x)
				prevgroup = x.InvFlag.flagID
		contents.append(group)
		return contents


	def getEftBlock(self):
		block = "[%s, %s's %s]\n\n" % (self.invType.typeName, self.character.characterName, self.invType.typeName)
		# Lows
		for i in range(1, (self.countLowSlots() + 1)):
			mod = self.getLowMod(i)
			charge = self.getLowCharge(i)
			if mod == None:
				block += "[Empty Low slot]\n"
			else:
				if charge == None:
					block += "%s\n" % mod.InvType.typeName
				else:
					block += "%s, %s\n" % (mod.InvType.typeName, charge.InvType.typeName)

		# Mids
		block += "\n"
		for i in range(1, (self.countMidSlots() + 1)):
			mod = self.getMidMod(i)
			charge = self.getMidCharge(i)
			if mod == None:
				block += "[Empty Mid slot]\n"
			else:
				if charge == None:
					block += "%s\n" % mod.InvType.typeName
				else:
					block += "%s, %s\n" % (mod.InvType.typeName, charge.InvType.typeName)

		# Highs
		block += "\n"
		for i in range(1, (self.countHighSlots() + 1)):
			mod = self.getHighMod(i)
			charge = self.getHighCharge(i)
			if mod == None:
				block += "[Empty High slot]\n"
			else:
				if charge == None:
					block += "%s\n" % mod.InvType.typeName
				else:
					block += "%s, %s\n" % (mod.InvType.typeName, charge.InvType.typeName)

		# Rigs
		block += "\n"
		for i in range(1, (self.countRigSlots() + 1)):
			mod = self.getRig(i)
			if mod == None:
				block += "[Empty Rig slot]\n"
			else:
				block += "%s\n" % mod.InvType.typeName

		# Drones
		drones = self.session.query(Asset, InvType, func.sum(Asset.quantity).label("quantity")).join(InvType).join(InvGroup).filter(Asset.locationID == self.asset.itemID, InvGroup.categoryID == 18).group_by(Asset.typeID).all()
		if len(drones) > 0:
			block += "\n\n"
			for x in drones:
				block += "%s x%d\n" % (x.InvType.typeName, x.quantity)

		# Cargo
		cargo = self.session.query(Asset, InvType, func.sum(Asset.quantity).label("quantity")).join(InvType).filter(Asset.locationID == self.asset.itemID, Asset.flag == 5).group_by(Asset.typeID).all()
		print cargo
		if len(cargo) > 0:
			block += "\n\n"
			for x in cargo:
				block += "%s x%d\n" % (x.InvType.typeName, x.quantity)

		return block

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
