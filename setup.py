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
	service_imcp1 = Service("ICMP (1)", "imcp", "check_imcp")
	service_imcp2 = Service("ICMP (2)", "imcp", "check_imcp")
	service_ad = Service("AD", "ldap", "check_ldap_lookup")
	service_http = Service("HTTP", "http", "check_custom_lockdownv1")
	service_ftp = Service("FTP", "ftp", "check_upload_download")
	service_imap = Service("IMAP", "imap", "check_imap_login")
	
	session.add_all([
		service_imcp1, service_imcp2, service_ad,
		service_http, service_ftp, service_imap
	])

	# Assign services to each team
	for i in range(config['TEAM_MIN_NUM'], config['TEAM_MAX_NUM']):
		# ICMP
		session.add_all([
			TeamService(teams[i], service_imcp1, "IP", "10.%d.1.15" % (i), edit=False),
			TeamService(teams[i], service_imcp1, "IP", "10.%d.1.25" % (i), edit=False),
			TeamService(teams[i], service_imcp2, "IP", "10.%d.1.67" % (i), edit=False),
			TeamService(teams[i], service_imcp2, "IP", "10.%d.1.77" % (i), edit=False)
		])

		# AD
		session.add_all([
			TeamService(teams[i], service_ad, "HOST", "10.%d.1.99" % (i), order=0),
			TeamService(teams[i], service_ad, "LOOKUP_USER", "ad\Administrator", edit=False, order=3),
			TeamService(teams[i], service_ad, "DOMAIN", "catflix%02d.cat" % (i), edit=False, order=1),

			# User's to use
			TeamService(teams[i], service_ad, "USERPASS", "jgeist||Changeme!", order=2),
			TeamService(teams[i], service_ad, "USERPASS", "jdroste||ego123!", order=2),
		])

		# HTTP
		session.add_all([
			TeamService(teams[i], service_http, "HOST", "10.%d.2.15" % (i), order=0),
			TeamService(teams[i], service_http, "PORT", "80", order=1),
			TeamService(teams[i], service_http, "PORT2", "32400", order=2),
		])

		# FTP
		session.add_all([
			TeamService(teams[i], service_ftp, "HOST", "10.%d.2.25" % (i), order=0),

			# User's to use
			TeamService(teams[i], service_ftp, "USERPASS", "plex||changeme", order=1),
		])

		# IMAP
		session.add_all([
			TeamService(teams[i], service_imap, "HOST", "10.%d.2.99" % (i), order=0),
			TeamService(teams[i], service_imap, "PORT", "587", order=1),

			# User's to use
			TeamService(teams[i], service_imap, "USERPASS", "kcleary@catflix%02d.cat||cats4cats" % (i), order=2)
		])

	# We're done! Commit (and hope it works..)
	session.commit()
	
except Exception as e:
	print "Error: %s" % (e)
	session.rollback()

	import traceback
	traceback.print_exc()
