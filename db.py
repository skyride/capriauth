import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import getConfig

def getEngine(echo=False):
	config = getConfig()
	config = config.db

	connect = 'mysql://%s:%s@%s:%d/' % (config.user, config.passw, config.host, config.port)
	engine = create_engine(connect, echo=echo)
	return engine


def getSession(echo=False):
	Session = sessionmaker(bind=getEngine(echo))
	session = Session()
	return session
