import config
import imaplib
import requests
import re
import socket


# DEFAULTS
imap_config = {
	'timeout': 15,
}
# /DEFAULTS

# CONFIG
if "imap" in config.CHECKS:
	imap_config.update(config.CHECKS["imap"])

socket.setdefaulttimeout(imap_config["timeout"])
# /CONFIG

def check_imap_login(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Successful authentication against the email server")
	check.addOutput("OUTPUT:\n")
	check.addOutput("Starting check...")

	try:
		check.addOutput("Connecting to %s:%s..." % (data["HOST"], data["PORT"]))
		imapObj = imaplib.IMAP4(data["HOST"], data["PORT"])
		check.addOutput("Connected!")

		check.addOutput("Logging in as %s..." % (data["USER"]))
		imapObj.login(data["USER"], data["PASS"])
		check.addOutput("Logged in!")

		# It passed all our check
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

	return

