from config import config
from scoring import engine, Session
from scoring.models import *

try:
	# Initalize DB
	session = Session()
	Base.metadata.drop_all(engine)
	Base.metadata.create_all(engine)

	# Create initial teams
	teams = {}
	for i in range(config['TEAM_MIN_NUM'], config['TEAM_MAX_NUM']):
		teams[i] = Team("Team %d" % (i))

		session.add(teams[i])

	# Create our services
	service_imcp = Service("IMCP", "imcp", "check_imcp")
	service_dns = Service("DNS", "dns", "check_dns")
	service_ad = Service("AD", "ldap", "check_ldap_lookup")
	service_http = Service("HTTP", "http", "check_custom_lockdownv0")
	service_mysql = Service("MySQL", "mysql", "check_query_server")
	service_ftp = Service("FTP", "ftp", "check_upload_download")

	service_example = Service("Example", "example", "check_example")
	
	session.add_all([
		service_example,
		service_imcp, service_dns, service_ad,
		service_http, service_mysql, service_ftp
	])

	# Assign services to each team
	for i in range(config['TEAM_MIN_NUM'], config['TEAM_MAX_NUM']):
		# ICMP
		session.add_all([
			TeamService(teams[i], service_imcp, "IP", "10.%d.1.101" % (i), edit=False),
			TeamService(teams[i], service_imcp, "IP", "10.%d.1.102" % (i), edit=False),
			TeamService(teams[i], service_imcp, "IP", "10.%d.1.201" % (i), edit=False),
			TeamService(teams[i], service_imcp, "IP", "10.%d.1.202" % (i), edit=False)
		])

		# DNS
		session.add_all([
			TeamService(teams[i], service_dns, "HOST", "10.%d.1.10" % (i), order=0),
			TeamService(teams[i], service_dns, "LOOKUP", "ad.obm%02d.open" % (i), edit=False, order=1),
			TeamService(teams[i], service_dns, "EXPECTED", "10.%d.1.10" % (i), edit=False, order=2)
		])

		# AD
		session.add_all([
			TeamService(teams[i], service_ad, "HOST", "10.%d.1.10" % (i), order=0),
			TeamService(teams[i], service_ad, "LOOKUP_USER", "ad\Administrator", edit=False, order=2),

			# User's to use
			TeamService(teams[i], service_ad, "USERPASS", "ad\mal||changeme", order=1)
		])

		# HTTP
		session.add_all([
			TeamService(teams[i], service_http, "HOST", "10.%d.2.50" % (i), order=0),
			TeamService(teams[i], service_http, "PORT", "80", order=1),

			# User's to use
			TeamService(teams[i], service_http, "USERPASS", "admin||changeme", order=2),
		])

		# MySQL
		session.add_all([
			TeamService(teams[i], service_mysql, "HOST", "10.%d.2.75" % (i), order=0),
			TeamService(teams[i], service_mysql, "PORT", "3306", order=1),
			TeamService(teams[i], service_mysql, "USER", "root", order=2),
			TeamService(teams[i], service_mysql, "PASS", "changeme", order=3),
			TeamService(teams[i], service_mysql, "DB_LOOKUP", "obm", edit=False, order=4),
		])

		# FTP
		session.add_all([
			TeamService(teams[i], service_ftp, "HOST", "10.%d.2.25" % (i), order=0),

			# User's to use
			TeamService(teams[i], service_ftp, "USERPASS", "ad\mal||changeme", order=1),
		])

	# We're done! Commit (and hope it works..)
	session.commit()
	
except Exception as e:
	print "Error: %s" % (e)
	session.rollback()

	import traceback
	traceback.print_exc()