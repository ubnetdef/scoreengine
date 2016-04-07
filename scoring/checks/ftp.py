from binascii import hexlify
from config import config
from ftplib import FTP
from os.path import basename
from os import urandom
from os.path import getsize
from random import choice
from tempfile import NamedTemporaryFile

# DEFAULTS
ftp_config = {
	'timeout': 5,
	'prefix': 'scoreengine_'
}
# /DEFAULTS

# CONFIG
if "ftp" in config:
	ftp_config.update(config["ftp"])
# /CONFIG

def check_upload_download(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful connect, upload, and deletion of a file")
	check.addOutput("OUTPUT:\n")

	# Create a temp file
	checkFile = NamedTemporaryFile(prefix=ftp_config["prefix"])

	# Write random amount of bytes to the checkFile
	# Size should be 2x randomBytes due to hexlify
	randomBytes = choice(range(1000, 9000))
	checkFile.write(hexlify(urandom(randomBytes)))
	checkFile.flush()

	checkFileName = basename(checkFile.name)
	checkFileSize = getsize(checkFile.name)
	ftp = None

	check.addOutput("Starting check...")

	try:
		# Start the connection
		check.addOutput("Connecting to %s..." % (data["HOST"]))
		ftp = FTP(data["HOST"], timeout=ftp_config["timeout"])
		check.addOutput("Connected!")

		# Login
		check.addOutput("Attempting to login as %s with password '%s'" % (data["USER"], data["PASS"]))
		ftp.login(data["USER"], data["PASS"])
		check.addOutput("Authentication sucessful!")

		# Attempt to upload a file
		check.addOutput("Uploading file %s with %d bytes..." % (checkFileName, checkFileSize))
		ftp.storlines("STOR " + checkFileName, checkFile)
		check.addOutput("Uploaded!")

		# Get the size of the file
		check.addOutput("Getting size of %s...." % (checkFileName))
		actualSize = ftp.size(checkFileName)
		if actualSize is not checkFileSize:
			check.addOutput("File size is %d, not the same as source (%d)! Failure!" % (actualSize, checkFileSize))

			ftp.quit()
			return
		else:
			check.addOutput("File size check passed!")

		# Delete it
		check.addOutput("Deleting file %s..." % (checkFileName))
		ftp.delete(checkFileName)
		check.addOutput("Deleted!")

		# Passed!
		ftp.quit()

		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

		if ftp is not None:
			ftp.quit()

		return