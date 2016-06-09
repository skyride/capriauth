import sys

from flask import Flask, Request, render_template
from flask.ext.login import LoginManager, UserMixin, login_required

from config import getConfig
from db import getSession
from models import *
from ships import *
from dispfuncs import *

# Setup
config = getConfig()
session = getSession()

reload(sys)
sys.setdefaultencoding("utf-8")
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# Jinja functions
app.jinja_env.globals.update(fitModHtml=fitModHtml)

@app.route("/")
def index():
	return render_template("index.html", config=config.auth)


@app.route("/viewship/<int:itemID>")
def viewship(itemID):
	# Check the ship exists
	ship = getShip(session=session, itemID=itemID)
	if ship == None:
		return render_template("404.html", config=config.auth, message="Specified ship could not be found")
	return render_template("viewship_fit.html", config=config.auth, ship=ship)


@app.route("/viewship")
def supercheck():
	session = getSession()
	supers = []

	#for x in session.query(Asset, InvType, Character, Corporation).join(InvType).join(Character).join(Corporation).filter(InvType.groupID.in_((659, 30))).order_by(InvType.groupID, InvType.typeID, Character.lastKnownLocation).all():
	for x in session.query(Asset, InvType, Character, Corporation).join(InvType).join(InvGroup).join(Character).join(Corporation).filter(InvGroup.categoryID == 6).filter(Asset.singleton == 1).order_by(InvType.groupID, InvType.typeID, Character.lastKnownLocation).all():
		sup = {}
		sup['ship'] = x.Asset
		sup['type'] = x.InvType
		sup['char'] = x.Character
		sup['corp'] = x.Corporation

		supers.append(sup)

	return render_template("viewship.html", config=config.auth, supers=supers)



@app.route("/protected/")
@login_required
def protected():
	return render_template("index.html", page_title="%s: Index" % auth_name, auth_name=auth_name, content="Hello Protected World!")

if __name__ == '__main__':
	app.run(debug=True)
