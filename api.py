import datetime
import time

from db import getSession
from eveapi import eveapi
from models import *

# Logging errors/messages on the API
def apiLog(errorMessage):
    timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]')
    errorLine = "%s %s" % (timeStamp, errorMessage)
    print errorLine



# Update the public information about a corporation, returns false if an error occurs
def upsertCorporation(eve, corporationID):
    try:
        # Check if we already have the corp in the database
        session = getSession()
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

        # Call the XMLAPI and update the object
        corpSheet = eve.corp.CorporationSheet(corporationID=corporationID)
        dbCorp.corporationName = corpSheet.corporationName
        dbCorp.ticker = corpSheet.ticker
        dbCorp.taxRate = corpSheet.taxRate
        dbCorp.memberCount = corpSheet.memberCount
        dbCorp.lastUpdated = datetime.datetime.now()
        if corpSheet.allianceID == 0:
            dbCorp.allianceID = None
        else:
            dbCorp.allianceID = corpSheet.allianceID

        # Commit the changes
        session.add(dbCorp)
        session.commit()
        return True
    except Exception as e:
        apiLog("Exception occurred doing public corp update on corporationID=%d: %s" % (corporationID, str(e)))
        return False



# Update everything about this API object in the database
def updateApiKey(session, api):
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
                apiLog("Deleting API ID %d as it has been deleted or expired" % api.id)
                session.delete(api)
                session.commit()
            else:
                apiLog("The XMLAPI returned an error [%d] checking API ID %d, lets try again later" % (e.code, api.id))
            return
        except Exception as e:
            apiLog("Generic Exception checking API ID %d: %s" % (api.id, str(e)))
            return

        # Update the key info
        api.accessMask = keyinfo.key.accessMask
        api.type = keyinfo.key.type
        api.lastUpdated = datetime.datetime.now()
        if keyinfo.key.expires == "":
            api.expires = None
        else:
            api.expires = datetime.datetime.fromtimestamp(keyinfo.key.expires)

        key = keyinfo.key

        # Purge characters from database that aren't on the API
        for dbChar in api.characters:
            if dbChar.characterID not in map(lambda x: x.characterID, key.characters):
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

        # Commit all of the updates to the database
        session.commit()

    # Exceptions for our main rollback try
    except eveapi.Error as e:
        apiLog("XMLAPI returned the following error: [%d] '%s'" % (e.code, e.message))
        session.rollback()
    except Exception as e:
        apiLog("Generic Exception: %s" % e.message)
        session.rollback()
