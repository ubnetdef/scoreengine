from binascii import hexlify
from config import config
from base64 import b64encode
from datetime import datetime, timedelta
from hashlib import sha1
from os import urandom
import requests
import re

# DEFAULTS
http_config = {
	'timeout': 5,
	'lockdownv0_random_bytes': 20,
	'lockdownv0_lateness': 30
}
# /DEFAULTS

# CONFIG
if "http" in config:
	http_config.update(config["http"])
# /CONFIG

def check_http(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Website is online")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		# Time the start of the request
		reqStart = datetime.now()

		# Connect to the website
		check.addOutput("Connecting to http://%s:%s" % (data["HOST"], data["PORT"]))
		session = requests.Session()
		req = session.get("http://%s:%s" % (data["HOST"], data["PORT"]), timeout=http_config["timeout"])
		check.addOutput("Connected!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

	return

def check_custom_lockdownv0(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful logging in of a user")
	check.addOutput("OUTPUT:\n")

	# Setup the cookie
	randomCheck = hexlify(urandom(http_config["lockdownv0_random_bytes"]))
	cookie = {
		'user': data["USER"],
		'pass': sha1(data["PASS"]).hexdigest(),
		'ie': randomCheck,
	}

	check.addOutput("Starting check...")

	try:
		# Time the start of the request
		reqStart = datetime.now()

		# Connect to the website
		check.addOutput("Connecting to http://%s:%s" % (data["HOST"], data["PORT"]))
		session = requests.Session()
		req = session.get("http://%s:%s" % (data["HOST"], data["PORT"]), timeout=http_config["timeout"], cookies=cookie)
		check.addOutput("Connected!")

		# Search for "x-injectengine-check"
		check.addOutput("Checking page...")
		matches = re.search("<meta name=\"x-injectengine-check\" content=\"(.*)\">", req.text)

		if matches is None:
			check.addOutput("Check failed on part 1!")
			return

		magicText = matches.group(1).split("|")

		if len(magicText) != 3:
			check.addOutput("Check failed on part 2!")
			return

		actualUsername = magicText[0]
		actualTime = datetime.fromtimestamp(int(magicText[1]))
		actualHash = magicText[2]

		expectedHash = sha1("%s%s%s%s" % (data["USER"], magicText[1], sha1(data["PASS"]).hexdigest(), randomCheck)).hexdigest()

		if b64encode(data["USER"]) != actualUsername:
			check.addOutput("Check failed on part 3!")
			return

		# Disabling this due to NTP issues on the linux boxes
		#if actualTime < reqStart - timedelta(seconds=http_config["lockdownv0_lateness"]):
		#	check.addOutput("Check failed on part 4!")
		#	return

		if actualHash != expectedHash:
			check.addOutput("Check failed on part 5!")
			return

		# It passed all our checks, gg.
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

		return