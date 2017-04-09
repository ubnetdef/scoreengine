from config import config
import MySQLdb

# DEFAULTS
mysql_config = {
	'timeout': 5,
	'min_tables_count': 0,
	'max_tables_count': -1,
}
# /DEFAULTS

# CONFIG
if "mysql" in config:
	mysql_config.update(config["mysql"])
# /CONFIG

def check_wordpress(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Login and query against a Wordpress Database")
	check.addOutput("OUTPUT:\n")

	# Connect to the DB
	check.addOutput("Starting check...")

	try:
		# Connect to the db
		check.addOutput("Connecting to %s:%s" % (data["HOST"], data["PORT"]))
		db = MySQLdb.connect(host=data["HOST"],
							port=int(data["PORT"]),
							user=data["USER"],
							passwd=data["PASS"],
							db=data["DB_LOOKUP"],
							connect_timeout=mysql_config["timeout"])
		check.addOutput("Connected!")

		cur = db.cursor()

		# Select the wordpress database
		check.addOutput("Querying for some data from the database...")
		cur.execute("SELECT option_value FROM wp_options WHERE option_name = 'blogname';")

		# Verify
		check.addOutput("Verifying the data...")
		if cur.rowcount != 1:
			check.addOutput("ERROR: Invalid data returned.")
			return

		db_data = cur.fetchone()
		if db_data[0] != data["BLOG_NAME"]:
			check.addOutput("ERROR: Invalid data returned.")
			return

		# We're done
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

		return


def check_query_server(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful login on the MySQL Database")
	check.addOutput("OUTPUT:\n")

	# Connect to the DB
	check.addOutput("Starting check...")

	try:
		# Connect to the db
		check.addOutput("Connecting to %s:%s" % (data["HOST"], data["PORT"]))
		db = MySQLdb.connect(host=data["HOST"],
							port=int(data["PORT"]),
							user=data["USER"],
							passwd=data["PASS"],
							db=data["DB_LOOKUP"],
							connect_timeout=mysql_config["timeout"])
		check.addOutput("Connected!")

		cur = db.cursor()

		# Attempt a show tables
		check.addOutput("Attempting to describe all tables...")
		cur.execute("SHOW tables;")

		# Verify tables
		if cur.rowcount < mysql_config["min_tables_count"]:
			check.addOutput("ERROR: The table count returned is incorrect.")
			return

		if mysql_config["max_tables_count"] > 0:
			if cur.rowcount > mysql_config["max_tables_count"]:
				check.addOutput("ERROR: The table count returned is incorrect.")
				return

		# We're done
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

		return