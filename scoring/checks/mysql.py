from config import config
import MySQLdb

# DEFAULTS
mysql_config = {
	'timeout': 5
}
# /DEFAULTS

# CONFIG
if "mysql" in config:
	mysql_config.update(config["mysql"])
# /CONFIG

def check_query_server(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful login on the MySQL Database")
	check.addOutput("OUTPUT:\n")

	# Connect to the DB
	check.addOutput("Starting check...")

	try:
		# Connect to the db
		check.addOutput("Connecting to %s:%s with %s (password: %s)" % (data["HOST"], data["PORT"], data["USER"], data["PASS"]))
		db = MySQLdb.connect(host=data["HOST"],
							port=int(data["PORT"]),
							user=data["USER"],
							passwd=data["PASS"],
							db=data["DB_LOOKUP"],
							connect_timeout=mysql_config["timeout"])
		check.addOutput("Connected!")

		cur = db.cursor()

		# Attempt a show tables
		check.addOutput("Attempting to select all users...")
		cur.execute("SELECT * FROM users")

		# Verify tables
		if cur.rowcount < 0:
			check.addOutput("ERROR: Nothing returned. Check your users table.")
			return

		# We're done
		check.setPassed()
		check.addOutput("Check sucessful!")
	except Exception as e:
		check.addOutput("ERROR: %s" % (e))

		return