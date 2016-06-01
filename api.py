import datetime
import time
import logging

from db import getSession
from eveapi import eveapi
from models import *
from config import getConfig

# Logging errors/messages on the API
def apiLog(errorMessage):
    timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]')
    errorLine = "%s %s" % (timeStamp, errorMessage)
    print errorLine


# Add an API key
# Returns an Api object on success, False if the key is invalid, an error message if it doesn't have enough permissions
def addApi(user, keyID, vCode, name, session=getSession()):
    try:
        if session.query(Api).filter(Api.keyID == keyID, Api.vCode==vCode).count() > 0:
            return "This API Key is already in the database"

        # We NEED APIKeyInfo, AccountStatus, CharacterSheet and AssetList
        eveapi.set_user_agent("eveapi.py/1.3")
        eve = eveapi.EVEAPIConnection()
        try:
            keyInfo = eve.account.APIKeyInfo(keyID=keyID, vCode=vCode)
            if keyInfo.key.type == "Corporation":
                return "This is a corp API, it's need to be a Character or Account API"
        except eveapi.Error as e:
            return "This API key is invalid or expired"
        try:
            accStatus = eve.account.AccountStatus(keyID=keyID, vCode=vCode)
            apiChar = eve.char.CharacterSheet(keyID=keyID, vCode=vCode, characterID=keyInfo.key.characters[0].characterID)
            assetList = eve.char.AssetList(keyID=keyID, vCode=vCode, characterID=keyInfo.key.characters[0].characterID, flat=1)
        except eveapi.Error as e:
            return "Your API key doesn't have enough permissions, at minimum it needs to be an active key with AccountStatus and CharacterInfo"

        # Build the key object
        api = Api()
        api.userId = user.id
        api.keyID = keyID
        api.vCode = vCode
        api.accessMask = keyInfo.key.accessMask
        api.type = keyInfo.key.type
        api.paidUntil = datetime.datetime.fromtimestamp(accStatus.paidUntil)
        api.createDate = datetime.datetime.fromtimestamp(accStatus.createDate)
        api.logonCount = accStatus.logonCount
        api.logonMinutes = accStatus.logonMinutes
        api.name = name
        api.lastUpdated = datetime.datetime.now()
        api.added = datetime.datetime.now()

        session.add(api)
        session.commit()

        # Now update the api key
        updateApiKey(session=session, api=api)

        return api

    except eveapi.Error as e:
        session.rollback()
        return "An error occurred on the EVE API, it's probably not your fault, try again later"
    except Exception as e:
        session.rollback()
        return "An error occurred querying this key: %s" % str(e)


# Recalculate a user's tags
# Takes a User object
def calculateTags(dbUser, session=None):
    # Create a session if one didn't already exist
    if session == None:
        session = getSession()
        commitOnEnd = True
    else:
        commitOnEnd = False

    # Get the config
    config = getConfig()

    # Get a set of the current tags
    currTags = map(lambda x: x.tag, session.query(Tag).filter(Tag.userId == dbUser.id).all())
    currTags = frozenset(currTags)
    newTags = []

    # Grab Ship Groups
    for x in session.query(Asset, InvGroup.groupName).join(InvType).join(InvGroup).join(Character).join(Api)\
    .filter(InvGroup.categoryID == 6,\
    Api.userId == dbUser.id).group_by(InvGroup.groupID).all():
        newTags.append("owns:%s" % x.groupName)

    # Grab Ship Types
    for x in session.query(Asset, InvType.typeName).join(InvType).join(InvGroup).join(Character).join(Api)\
    .filter(InvGroup.categoryID == 6,\
    Api.userId == dbUser.id).group_by(InvType.typeID).all():
        newTags.append("owns:%s" % x.typeName)

    # Grab skills (via chars in your membership)
    for x in session.query(Character, Corporation.corporationID, Corporation.allianceID).join(Corporation).join(Api).join(User).filter(User.id == dbUser.id).all():
        # Check if the character meets any of the membership requirements
        for test in config.auth.members:
            if test.type not in ["alliance", "corporation"]:
                continue

            if test.type == "alliance" and x.allianceID != test.id:
                print x
                continue
            if test.type == "corporation" and x.corporationID != test.id:
                continue

            # If we've reached here, the character meets the requirements
            for skill in session.query(Skill, InvType.typeName).join(InvType).filter(Skill.characterID == x.Character.characterID).all():
                newTags.append("has:%s" % skill.typeName)
                if skill.Skill.level == 5 and skill.Skill.skillpoints >= 1280000:
                    newTags.append("has:%s 5" % skill.typeName)

    # Purge old sets
    for x in frozenset(currTags).difference(newTags):
        session.delete(session.query(Tag).filter(Tag.userId == dbUser.id, Tag.tag == x).first())

    # Add new sets
    for x in frozenset(newTags).difference(currTags):
        newTag = Tag()
        newTag.userId = dbUser.id
        newTag.tag = x
        session.add(newTag)

    # Commit the session as it was created within this method
    if commitOnEnd == True:
        session.commit()


# Update the public information about an alliance, returns false if an error occurs
def upsertAlliance(eve, allianceID, session=None):
    try:
        if session == None:
            session = getSession()
            commitOnEnd = True
        else:
            commitOnEnd = False

        # Check if we already have the alliance in the database
        query = session.query(Alliance).filter(Alliance.allianceID == allianceID)
        if query.count() > 0:
            dbAlliance = query[0]
            # Don't update if it's been done within the last 6hrs
            if (dbAlliance.lastUpdated + datetime.timedelta(0, 21600)) > datetime.datetime.now():
                return True
        else:
            # Create the Alliance object
            dbAlliance = Alliance()
            dbAlliance.allianceID = allianceID

        # Call the XMLAPI
        allianceList = eve.eve.AllianceList(version=1)
        indAllianceList = allianceList.alliances.IndexedBy("allianceID")
        apiAlliance = indAllianceList.Get(allianceID)

        # Update the object
        dbAlliance.allianceName = apiAlliance.name
        dbAlliance.ticker = apiAlliance.shortName
        dbAlliance.memberCount = apiAlliance.memberCount
        dbAlliance.startDate = datetime.datetime.fromtimestamp(apiAlliance.startDate)
        dbAlliance.lastUpdated = datetime.datetime.now()

        # Commit the changes
        session.add(dbAlliance)
        if commitOnEnd == True:
            session.commit()
        return True

    except Exception as e:
        apiLog("Exception occurred doing public alliance update on allianceID=%d: %s" % (allianceID, str(e)))
        session.rollback()
        return False



# Update the public information about a corporation, returns false if an error occurs
def upsertCorporation(eve, corporationID, session=None):
    try:
        if session == None:
            session = getSession()
            commitOnEnd = True
        else:
            commitOnEnd = False

        # Check if we already have the corp in the database
        query = session.query(Corporation).filter(Corporation.corporationID == corporationID)
        if query.count() > 0:
            dbCorp = query[0]
            # Don't update if it's been done within the last 6hrs
            if (dbCorp.lastUpdated + datetime.timedelta(0, 21600)) > datetime.datetime.now():
                return True
        else:
            # Create the Corporation object
            dbCorp = Corporation()
            dbCorp.corporationID = corporationID

        # Call the XMLAPI
        corpSheet = eve.corp.CorporationSheet(corporationID=corporationID)

        # Update the object
        dbCorp.corporationName = corpSheet.corporationName
        dbCorp.ticker = corpSheet.ticker
        dbCorp.taxRate = corpSheet.taxRate
        dbCorp.memberCount = corpSheet.memberCount
        dbCorp.lastUpdated = datetime.datetime.now()
        if corpSheet.allianceID == 0:
            dbCorp.allianceID = None
        else:
            # Upsert the alliance
            if not upsertAlliance(eve=eve, allianceID=corpSheet.allianceID):
                apiLog("An error occurred upserting allianceID=%d, so we'll rollback and try later" % corpSheet.allianceID)
                session.rollback()
                return False
            dbCorp.allianceID = corpSheet.allianceID

        # Commit the changes
        session.add(dbCorp)
        if commitOnEnd == True:
            session.commit()
        return True

    except Exception as e:
        apiLog("Exception occurred doing public corp update on corporationID=%d: %s" % (corporationID, str(e)))
        session.rollback()
        return False



# Update everything about this API object in the database
def updateApiKey(api, session=getSession()):
    eveapi.set_user_agent("eveapi.py/1.3")
    eve = eveapi.EVEAPIConnection()

    # Open our main rollback try
    try:
        # Check that the API is still active...
        try:
            keyinfo = eve.account.APIKeyInfo(keyID=api.keyID, vCode=api.vCode)
        except eveapi.Error as e:
            # ...and delete the api if it isn't
            if e.code == 403:
                apiLog("\tDeleting API ID %d as it has been deleted or expired" % api.id)
                session.delete(api)
                session.commit()
            else:
                apiLog("The XMLAPI returned an error [%d] checking API ID %d, lets try again later" % (e.code, api.id))
            return
        except Exception as e:
            apiLog("Generic Exception checking API ID %d: %s" % (api.id, str(e)))
            return

        # Grab AccountStatus too
        accStatus = eve.account.AccountStatus(keyID=api.keyID, vCode=api.vCode)

        # Update the key info
        api.accessMask = keyinfo.key.accessMask
        api.type = keyinfo.key.type
        api.paidUntil = datetime.datetime.fromtimestamp(accStatus.paidUntil)
        api.createDate = datetime.datetime.fromtimestamp(accStatus.createDate)
        api.logonCount = accStatus.logonCount
        api.logonMinutes = accStatus.logonMinutes
        api.lastUpdated = datetime.datetime.now()
        if keyinfo.key.expires == "":
            api.expires = None
        else:
            api.expires = datetime.datetime.fromtimestamp(keyinfo.key.expires)

        key = keyinfo.key

        # Purge characters from database that aren't on the API
        for dbChar in api.characters:
            if dbChar.characterID not in map(lambda x: x.characterID, key.characters):
                apiLog("Deleted character as they were no longer on the API characterID=%d, characterName=%s" % (dbChar.characterID, dbChar.characterName))
                session.delete(dbChar)

        # Add or update characters from the API into the database
        for apiChar in key.characters:
            if apiChar.characterID not in map(lambda x: x.characterID, api.characters):
                dbChar = Character()
                dbChar.characterID = apiChar.characterID
                dbChar.apiId = api.id
                session.add(dbChar)
            else:
                for dbChar in api.characters:
                    if dbChar.characterID == apiChar.characterID:
                        # Suppresed this check as it doesn't make logical sense to limit it this far down stream
                        # Check its not been updated within the last 119 mins
                        #if (dbChar.lastUpdated + datetime.timedelta(0, 7140)) > datetime.datetime.now():
                        #    return
                        break

            # Get the CharacterSheet
            charSheet = eve.char.CharacterSheet(keyID=api.keyID, vCode=api.vCode, characterID=apiChar.characterID)

            # Upsert the corporation
            if not upsertCorporation(eve=eve, corporationID=charSheet.corporationID):
                apiLog("An error occurred upserting corporationID=%d, so we'll rollback and try later" % charSheet.corporationID)
                session.rollback()
                return

            # Update the characters values
            dbChar.characterName = apiChar.characterName
            dbChar.corporationID = apiChar.corporationID
            dbChar.factionID = apiChar.factionID
            dbChar.balance = charSheet.balance
            dbChar.cloneJumpDate = datetime.datetime.fromtimestamp(charSheet.cloneJumpDate)
            dbChar.jumpActivation = datetime.datetime.fromtimestamp(charSheet.jumpActivation)
            dbChar.jumpFatigue = datetime.datetime.fromtimestamp(charSheet.jumpFatigue)
            dbChar.jumpLastUpdate = datetime.datetime.fromtimestamp(charSheet.jumpLastUpdate)
            dbChar.DoB = datetime.datetime.fromtimestamp(charSheet.DoB)
            dbChar.remoteStationDate = datetime.datetime.fromtimestamp(charSheet.remoteStationDate)
            dbChar.homeStationID = charSheet.homeStationID
            dbChar.lastUpdated = datetime.datetime.now()

            # Get the Asset List
            assetList = eve.char.AssetList(keyID=api.keyID, vCode=api.vCode, characterID=apiChar.characterID, flat=1)
            apiAssetsById = assetList.assets.IndexedBy("itemID")

            # Purge assets from the database that aren't on the API
            #dbAssets = session.query(Asset).filter(Asset.characterID == apiChar.characterID).all()
            for dbAsset in session.query(Asset).filter(Asset.characterID == apiChar.characterID).all():
                try:
                    apiAssetsById.Get(dbAsset.itemID)
                except:
                    session.delete(dbAsset)

            # Add or update assets from the API into the database
            dbAssets = session.query(Asset).filter(Asset.characterID == apiChar.characterID).all()
            dbAssetsDict = {}
            for dbAsset in dbAssets:
                dbAssetsDict[dbAsset.itemID] = dbAsset
            newAssets = []
            dbAssetSet = frozenset(frozenset(map(lambda x: x.itemID, dbAssets)))
            for apiAsset in assetList.assets:
                if apiAsset.itemID not in dbAssetSet:
                    dbAsset = Asset()
                    dbAsset.itemID = apiAsset.itemID
                    dbAsset.characterID = apiChar.characterID
                    newAssets.append(dbAsset)
                else:
                    dbAsset = dbAssetsDict[apiAsset.itemID]

                # Update the asset values
                dbAsset.locationID = apiAsset.locationID
                dbAsset.typeID = apiAsset.typeID
                dbAsset.quantity = apiAsset.quantity
                dbAsset.flag = apiAsset.flag
                dbAsset.singleton = apiAsset.singleton

            # Add the assets to the session
            session.add_all(newAssets)

            # Add or update skills from the API into the database
            newSkills = []
            dbSkillsDict = {}
            for dbSkill in dbChar.skills:
                dbSkillsDict[dbSkill.typeID] = dbSkill
            dbSkillSet = frozenset(map(lambda x: "%d:%d" % (x.characterID, x.typeID), dbChar.skills))
            for apiSkill in charSheet.skills:
                if "%d:%d" % (apiChar.characterID, apiSkill.typeID) not in dbSkillSet:
                    dbSkill = Skill()
                    dbSkill.characterID = apiChar.characterID
                    dbSkill.typeID = apiSkill.typeID
                    newSkills.append(dbSkill)
                else:
                    dbSkill = dbSkillsDict[apiSkill.typeID]

                # Update the skills values
                dbSkill.level = apiSkill.level
                dbSkill.skillpoints = apiSkill.skillpoints

            # Add the skills to the session
            session.add_all(newSkills)

            # Log line
            apiLog("\tUpdated characterID=%d, characterName='%s'" % (dbChar.characterID, dbChar.characterName))


        # Commit all of the updates to the database
        session.commit()

    # Exceptions for our main rollback try
    except eveapi.Error as e:
        if e.code == 403:
            session.rollback()
            session.delete(api)
            session.commit()
            apiLog("\tDeleted API as it has lost permissions we need, into the trash you go")
        else:
            apiLog("\tXMLAPI returned the following error: [%d] '%s'" % (e.code, e.message))
        session.rollback()
    #except Exception as e:
    #    apiLog("Generic Exception: %s" % str(e))
    #    session.rollback()
