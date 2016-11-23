from config import config
import requests
import re
import smtplib

# DEFAULTS
imap_config = {
	'timeout': 5,
}
# /DEFAULTS

# CONFIG
if "imap" in config:
	imap_config.update(config["imap"])
# /CONFIG

def check_imap_login(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Successful authentication against the email server")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		check.addOutput("Connecting to %s:%s..." % (data["HOST"], data["PORT"]))
		smtpObj = smtplib.SMTP(data["HOST"], data["PORT"])
		check.addOutput("Connected!")

		smtpObj.ehlo()
		smtpObj.starttls()

		check.addOutput("Logging in as %s..." % (data["USER"]))
		smtpObj.login(data["USER"], data["PASS"])
		check.addOutput("Logged in!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

	return

