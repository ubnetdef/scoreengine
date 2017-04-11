from base64 import b64encode
from binascii import hexlify
from datetime import datetime, timedelta
from fake_useragent import UserAgent
from hashlib import sha1
from os import urandom
import config
import requests
import re

# DEFAULTS
http_config = {
	'timeout': 15,

	'wordpress_login': 'wp-login.php',
	'wordpress_cookie': 'wordpress_logged_in_',
}
# /DEFAULTS

# CONFIG
if "http" in config.CHECKS:
	http_config.update(config.CHECKS["http"])

http_headers = {
	"Connection": "close",
	"User-Agent": UserAgent().random
}
# /CONFIG

def check_http(check, data):
	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("EXPECTED: Website is online")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		# Time the start of the request
		reqStart = datetime.now()

		# Connect to the website
		check.addOutput("Connecting to http://{HOST}:{PORT}".format(**data))
		session = requests.Session()
		req = session.get("http://{HOST}:{PORT}".format(**data), timeout=http_config["timeout"], headers=http_headers)

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code {}".format(req.status_code))
			return

		check.addOutput("Connected!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: {}: {}".format(type(e).__name__, e))

	return

def check_wordpress(check, data):
	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("EXPECTED: Ability to use the wordpress website")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		# Time the start of the request
		reqStart = datetime.now()

		# Connect to the website
		check.addOutput("Connecting to http://{HOST}:{PORT}".format(**data))
		session = requests.Session()
		req = session.get("http://{HOST}:{PORT}".format(**data), timeout=http_config["timeout"], headers=http_headers)

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code {}".format(req.status_code))
			return

		check.addOutput("Connected!")

		# Load the login page
		login_url = "http://{HOST}:{PORT}/{wordpress_login}".format(wordpress_login=http_config["wordpress_login"], **data)
		login_payload = {
			'log': data["USER"],
			'pwd': data["PASS"]
		}

		check.addOutput("Loading login page")
		req = session.get(login_url, timeout=http_config["timeout"], headers=http_headers)

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code {}".format(req.status_code))
			return

		check.addOutput("Loaded!")

		# Attempt to login
		check.addOutput("Attempting to login")
		req = session.post(login_url, data=login_payload, timeout=http_config["timeout"], headers=http_headers)

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code {}".format(req.status_code))
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
		check.addOutput("ERROR: {}: {}".format(type(e).__name__, e))

	return
