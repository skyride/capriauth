import json
from dotmap import DotMap

def getConfig():
	with open("config.json") as jfile:
		config = json.load(jfile)
		config = DotMap(config)
		return config
