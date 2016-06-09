import sqlalchemy
from sqlalchemy import ForeignKey, Column, Integer, BigInteger, Float, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import coalesce

from config import getConfig


Base = declarative_base()
config = getConfig().db

# User Class - auth.users
class User(Base):
	__tablename__ = "users"
	__table_args__ = {'schema': config.authdb }

	id = Column(Integer, primary_key=True)
	username = Column(String(32), unique=True)
	password = Column(String(40))
	email = Column(String(256))
	registeredOn = Column(DateTime)
	active = Column(Boolean)

	apis = relationship("Api", back_populates="user")
	logins = relationship("Login", back_populates="user", passive_deletes=True)
	tags = relationship("Tag", back_populates="user")

	def __repr__(self):
		return "<User(id=%d, username='%s')>" % (self.id, self.username)


# Login Class - auth.logins
class Login(Base):
	__tablename__ = "logins"
	__table_args__ = {'schema': config.authdb }

	id = Column(Integer, primary_key=True)
	userId = Column(Integer, ForeignKey("%s.users.id" % config.authdb))
	date = Column(DateTime)
	ip = Column(String(15))
	channel = Column(String(12))

	user = relationship("User", back_populates="logins")

	def __repr__(self):
		return "<Login(id=%d, userId=%d, username='%s', date='%s')>" % (self.id, self.userId, self.user.username, self.date)


# Alliance Class - auth.alliances
class Alliance(Base):
	__tablename__ = "alliances"
	__table_args__ = {'schema': config.authdb }

	allianceID = Column(BigInteger, primary_key=True)
	allianceName = Column(String(64))
	ticker = Column(String(5))
	memberCount = Column(Integer)
	startDate = Column(DateTime)
	lastUpdated = Column(DateTime)

	corporations = relationship("Corporation", back_populates="alliance")

	def __repr__(self):
		return "<Alliance(allianceID=%d, allianceName='%s', ticker='%s')>" % (self.allianceID, self.allianceName, self.ticker)


# Corporation Class - auth.corporations
class Corporation(Base):
	__tablename__ = "corporations"
	__table_args__ = {'schema': config.authdb }

	corporationID = Column(BigInteger, primary_key=True)
	corporationName = Column(String(64))
	ticker = Column(String(5))
	allianceID = Column(BigInteger, ForeignKey("%s.alliances.allianceID" % config.authdb))
	taxRate = Column(Float(3,2))
	memberCount = Column(Integer)
	lastUpdated = Column(DateTime)

	alliance = relationship("Alliance", back_populates="corporations")
	characters = relationship("Character", back_populates="corporation")

	def __repr__(self):
		return "<Corporation(corporationID=%d, corporationName='%s', ticker='%s', memberCount=%d)>" % (self.corporationID, self.corporationName, self.ticker, self.memberCount)


# Character Class - auth.characters
class Character(Base):
	__tablename__ = "characters"
	__table_args__ = {'schema': config.authdb }

	characterID = Column(BigInteger, primary_key=True)
	characterName = Column(String(64))
	corporationID = Column(BigInteger, ForeignKey("%s.corporations.corporationID" % config.authdb))
	factionID = Column(Integer)
	apiId = Column(Integer, ForeignKey("%s.apis.id" % config.authdb))
	balance = Column(Float(18, 2))
	cloneJumpDate = Column(DateTime)
	jumpActivation = Column(DateTime)
	jumpFatigue = Column(DateTime)
	jumpLastUpdate = Column(DateTime)
	DoB = Column(DateTime)
	remoteStationDate = Column(DateTime)
	homeStationID = Column(BigInteger)
	shipTypeID = Column(Integer)
	shipName = Column(String(40))
	lastKnownLocation = Column(String(128))
	lastUpdated = Column(DateTime)

	corporation = relationship("Corporation", back_populates="characters")
	skills = relationship("Skill", back_populates="character", passive_deletes=True)
	api = relationship("Api", back_populates="characters")
	jumpClones = relationship("JumpClone", back_populates="character")

	def __repr__(self):
		return "<Character(characterID=%d, characterName='%s', balance=%d, lastUpdated='%s')>" % (self.characterID, self.characterName, self.balance, self.lastUpdated)


# API Key Class - auth.apis
class Api(Base):
	__tablename__ = "apis"
	__table_args__ = {'schema': config.authdb }

	id = Column(Integer, primary_key=True)
	userId = Column(Integer, ForeignKey("%s.users.id" % config.authdb))
	keyID = Column(Integer)
	vCode = Column(String(64))
	type = Column(String(11))
	expires = Column(DateTime, nullable=True)
	accessMask = Column(Integer)
	paidUntil = Column(DateTime)
	createDate = Column(DateTime)
	logonCount = Column(BigInteger)
	logonMinutes = Column(BigInteger)
	name = Column(String(64))
	lastUpdated = Column(DateTime)
	added = Column(DateTime)

	user = relationship("User", back_populates="apis")
	characters = relationship("Character", passive_deletes=True)


	def __repr__(self):
		return "<Api(id=%d, userId=%d, username='%s', keyID=%d)>" % (self.id, self.userId, self.user.username, self.keyID)


# InvMarketGroup Class - sde.invMarketGroups
class InvMarketGroup(Base):
	__tablename__ = "invMarketGroups"
	__table_args__ = {'schema': config.sdedb }

	marketGroupID = Column(Integer, ForeignKey("%s.invMarketGroups.parentGroupID" % config.sdedb), primary_key=True)
	parentGroupID = Column(Integer, ForeignKey("%s.invMarketGroups.marketGroupID" % config.sdedb))
	marketGroupName = Column(String(100))
	description = Column(String(3000))
	iconID = Column(Integer)
	hasTypes = Column(Integer)

	parentGroup = relationship("InvMarketGroup", foreign_keys=[marketGroupID])
	childGroups = relationship("InvMarketGroup", foreign_keys=[parentGroupID])
	types = relationship("InvType")

	def __repr__(self):
		return "<InvMarketGroup(marketGroupID=%d, marketGroupName='%s', parentGroupID=%d)>" % (self.marketGroupID, self.marketGroupName, self.parentGroupID)


# InvCategory Class - sde.invCategories
class InvCategory(Base):
	__tablename__ = "invCategories"
	__table_args__ = {'schema': config.sdedb }

	categoryID = Column(Integer, primary_key=True)
	categoryName = Column(String(100))
	iconID = Column(Integer)
	published = Column(Integer)

	groups = relationship("InvGroup", back_populates="category")

	def __repr__(self):
		return "<InvCategory(categoryID=%d, categoryName='%s')>" % (self.categoryID, self.categoryName)


# InvGroup Class - sde.invGroups

class InvGroup(Base):
	__tablename__ = "invGroups"
	__table_args__ = {'schema': config.sdedb }

	groupID = Column(Integer, primary_key=True)
	categoryID = Column(Integer, ForeignKey("%s.invCategories.categoryID" % config.sdedb))
	groupName = Column(String(100))
	iconID = Column(Integer)
	useBasePrice = Column(Integer)
	anchored = Column(Integer)
	fittableNonSingleton = Column(Integer)
	published = Column(Integer)

	category = relationship("InvCategory", back_populates="groups")
	types = relationship("InvType", back_populates="group")

	def __repr__(self):
		return "<InvGroup(groupID=%d, groupName='%s', categoryID=%d>" % (self.groupID, self.groupName, self.categoryID)


# InvType Class - sde.invTypes
class InvType(Base):
	__tablename__ = "invTypes"
	__table_args__ = {'schema': config.sdedb }

	typeID = Column(Integer, primary_key=True)
	groupID = Column(Integer, ForeignKey("%s.invGroups.groupID" % config.sdedb))
	typeName = Column(String(100))
	description = Column(String)
	mass = Column(Float)
	volume = Column(Float)
	capacity = Column(Float)
	portionSize = Column(Integer)
	raceID = Column(Integer)
	basePrice = Column(Float)
	published = Column(Integer)
	marketGroupID = Column(Integer, ForeignKey("%s.invMarketGroups.marketGroupID" % config.sdedb))
	iconID = Column(Integer)
	soundID = Column(Integer)
	graphicID = Column(Integer)

	group = relationship("InvGroup", back_populates="types")
	marketGroup = relationship("InvMarketGroup", back_populates="types")
	attributes = relationship("DgmTypeAttribute", back_populates="type")

	def __repr__(self):
		return "<InvType(typeID=%d, typeName='%s', groupID=%d)>" % (self.typeID, self.typeName, self.groupID)


# Skill Class - auth.skills
class Skill(Base):
	__tablename__ = "skills"
	__table_args__ = {'schema': config.authdb }

	characterID = Column(BigInteger, ForeignKey("%s.characters.characterID" % config.authdb), primary_key=True)
	typeID = Column(Integer, ForeignKey("%s.invTypes.typeID" % config.sdedb), primary_key=True)
	level = Column(Integer)
	skillpoints = Column(Integer)

	character = relationship("Character", back_populates="skills")
	type = relationship("InvType")

	def __repr__(self):
		return "<Skill(characterID=%d, typeID=%d, typeName='%s', level=%d, skillpoints=%d)>" % (self.characterID, self.typeID, self.type.typeName, self.level, self.skillpoints)


# Asset Class - auth.assets
class Asset(Base):
	__tablename__ = "assets"
	__table_args__ = {'schema': config.authdb }

	itemID = Column(BigInteger, primary_key=True)
	locationID = Column(BigInteger)
	typeID = Column(Integer, ForeignKey("%s.invTypes.typeID" % config.sdedb))
	quantity = Column(BigInteger)
	flag = Column(Integer, ForeignKey("%s.invFlags.flagID" % config.sdedb))
	singleton = Column(Boolean)
	characterID = Column(BigInteger, ForeignKey("%s.characters.characterID" % config.authdb), primary_key=True)

	type = relationship("InvType")
	character = relationship("Character")
	invFlag = relationship("InvFlag")
	packagedVolume = relationship("InvVolume", uselist=False)

	def volume(self, quantity=None):
		if quantity == None:
			quantity = self.quantity
		else:
			quantity = int(quantity)
		if self.singleton == False:
			print self.packagedVolume
			if self.packagedVolume != None:
				return self.packagedVolume.volume * quantity
			
		return self.type.volume * quantity

	def __repr__(self):
		return "<Asset(itemID=%d, locationID=%d, typeID=%d, quantity=%d, characterID=%d)>" % (self.itemID, self.locationID, self.typeID, self.quantity, self.characterID)

# InvFlag Class - sde.invFlags
class InvFlag(Base):
	__tablename__ = "invFlags"
	__table_args__ = {'schema': config.sdedb }

	flagID = Column(Integer, primary_key=True)
	flagName = Column(String(200))
	flagText = Column(String(100))
	orderID = Column(Integer)

	def __repr__(self):
		return "<InvFlag(flagID=%d, flagName='%s, orderID=%d')>" % (self.flagID, self.flagName, self.orderID)

# InvVolume Class - sde.invVolumes
class InvVolume(Base):
	__tablename__ = "invVolumes"
	__table_args__ = {'schema': config.sdedb }

	typeid = Column(Integer, ForeignKey("%s.assets.typeID" % config.authdb), primary_key=True)
	volume = Column(Integer)

	def __repr__(self):
		return "<InvVolume(typeid=%d, volume=%d)>" % (self.typeid, self.volume)


# Tag Class - auth.tags
class Tag(Base):
	__tablename__ = "tags"
	__table_args__ = {'schema': config.authdb }

	userId = Column(Integer, ForeignKey("%s.users.id" % config.authdb), primary_key=True)
	tag = Column(String(64), primary_key=True)

	user = relationship("User", back_populates="tags")

	def __repr__(self):
		return "<Tag(tag='%s', userId=%d)>" % (self.tag, self.userId)


# Jump Clone Class - auth.jumpClones
class JumpClone(Base):
	__tablename__ = "jumpClones"
	__table_args__ = {'schema': config.authdb }

	jumpCloneID = Column(BigInteger, primary_key=True)
	characterID = Column(BigInteger, ForeignKey("%s.characters.characterID" % config.authdb))
	cloneName = Column(String(64))
	typeID = Column(Integer, ForeignKey("%s.invTypes.typeID" % config.sdedb))
	locationID = Column(BigInteger)

	character = relationship("Character", back_populates="jumpClones")
	implants = relationship("Implant", back_populates="jumpClone")
	type = relationship("InvType")

	def __repr__(self):
		return "<JumpClone(jumpCloneID=%d, characterID=%d, cloneName='%s')>" % (self.jumpCloneID, self.characterID, self.cloneName)


# Implant Class - auth.implants
class Implant(Base):
	__tablename__ = "implants"
	__table_args__ = {'schema': config.authdb }

	id = Column(Integer, primary_key=True)
	characterID = Column(BigInteger, ForeignKey("%s.characters.characterID" % config.authdb))
	jumpCloneID = Column(BigInteger, ForeignKey("%s.jumpClones.jumpCloneID" % config.authdb))
	typeID = Column(Integer, ForeignKey("%s.invTypes.typeID" % config.sdedb))

	character = relationship("Character")
	jumpClone = relationship("JumpClone", back_populates="implants")
	type = relationship("InvType")

	def __repr__(self):
		return "<Implant(id=%d, characterID=%d, typeID=%d, jumpCloneID=%s)>" % (self.id, self.characterID, self.typeID, self.jumpCloneID)


class DgmTypeAttribute(Base):
	__tablename__ = "dgmTypeAttributes"
	__table_args__ = {'schema': config.sdedb }

	typeID = Column(Integer, ForeignKey("%s.invTypes.typeID" % config.sdedb), primary_key=True)
	attributeID = Column(Integer, ForeignKey("%s.dgmAttributeTypes.attributeID" % config.sdedb), primary_key=True)
	valueInt = Column(Integer)
	valueFloat = Column(Float)

	def value(self):
		if self.valueInt == None:
			return self.valueFloat
		else:
			return self.valueInt

	type = relationship("InvType", back_populates="attributes")

	def __repr__(self):
		return "<DgmTypeAttribute(typeID=%d, attributeID=%d)>" % (self.typeID, self.attributeID)
