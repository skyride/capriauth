from flask import Flask, Request, render_template
from flask.ext.login import LoginManager, UserMixin, login_required

from config import getConfig

# Setup
config = getConfig()

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

@app.route("/")
def index():
	return render_template("index.html", config=config.auth)

@app.route("/protected/")
@login_required
def protected():
	return render_template("index.html", page_title="%s: Index" % auth_name, auth_name=auth_name, content="Hello Protected World!")

if __name__ == '__main__':
	app.run(debug=True)
