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

	'gitlab_login': 'users/sign_in',
	'gitlab_cookie': '_gitlab_session',
}
# /DEFAULTS

# CONFIG
if "http" in config.CHECKS:
	http_config.update(config.CHECKS["http"])

FAKE_UA = UserAgent(fallback='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')

http_headers = {
	"Connection": "close",
	"User-Agent": FAKE_UA.random
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
		login_url = "http://{HOST}:{PORT}/{login}".format(login=http_config["wordpress_login"], **data)
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

def check_gitlab(check, data):
	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("EXPECTED: Ability to use the gitlab website")
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
		check.addOutput("Loading login page")
		login_url = "http://{HOST}:{PORT}/{login}".format(login=http_config["gitlab_login"], **data)
		req = session.get(login_url, timeout=http_config["timeout"], headers=http_headers)
		matches = re.search('name="authenticity_token" value="([^"]+)"', req.content)

		if not matches:
			check.addOutput("ERROR: Login page did not contain needed information")
			return

		# Attempt a login
		login_payload = {
			'user[login]': data["USER"],
			'user[password]': data["PASS"],
			'authenticity_token': matches.group(1)
		}

		check.addOutput("Attempting login")
		req = session.get(login_url, timeout=http_config["timeout"], headers=http_headers)

		if req.status_code != 200:
			check.addOutput("ERROR: Page returned status code {}".format(req.status_code))
			return

		check.addOutput("Loaded!")

		# Check the cookies
		has_login_cookie = False
		for c in session.cookies:
			if http_config["gitlab_cookie"] in c.name:
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