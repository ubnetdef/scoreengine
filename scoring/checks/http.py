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

	'wordpress_login': 'wp-login.php',
	'wordpress_cookie': 'wordpress_logged_in_',
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

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code %d" % (req.status_code))
			return

		check.addOutput("Connected!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

	return

def check_wordpress(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Ability to use the wordpress website")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		# Time the start of the request
		reqStart = datetime.now()

		# Connect to the website
		check.addOutput("Connecting to http://%s:%s" % (data["HOST"], data["PORT"]))
		session = requests.Session()
		req = session.get("http://%s:%s" % (data["HOST"], data["PORT"]), timeout=http_config["timeout"])

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code %d" % (req.status_code))
			return

		check.addOutput("Connected!")

		# Load the login page
		login_url = "http://%s:%s/%s" % (data["HOST"], data["PORT"], http_config["wordpress_login"])
		login_payload = {
			'log': data["USER"],
			'pwd': data["PASS"]
		}

		check.addOutput("Loading login page")
		req = session.get(login_url, timeout=http_config["timeout"])

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code %d" % (req.status_code))
			return

		check.addOutput("Loaded!")

		# Attempt to login
		check.addOutput("Attempting to login")
		req = session.post(login_url, data=login_payload, timeout=http_config["timeout"])

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code %d" % (req.status_code))
			return

		# Check the cookies
		has_login_cookie = False
		for c in session.cookies:
			if http_config["wordpress_cookie"] in c.name:
				has_login_cookie = True

		if not has_login_cookie:
			check.addOutput("ERROR: Logged in cookie not set.")
			return

		check.addOutput("Logged in!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

	return
