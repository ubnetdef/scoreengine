###########################################################
###############  DO NOT EDIT THIS SECTION!  ###############
###########################################################

import os

class _Service:
	def __init__(self, group, check, *data):
		self.group = group
		self.check = check
		self.data = data

class _Data:
	def __init__(self, key, value, **kwargs):
		self.key = key
		self.value = value
		self.kwargs = kwargs


###########################################################
####################  EDIT BELOW HERE  ####################
###########################################################

DATABASE_URI = "mysql://user:pass@localhost:3306/scoreengine"
DATABASE_EXTRA = {
	"pool_size": 40,
	"max_overflow": 60,
}

BANK = {
	"SERVER": "localhost",
	"USER": "username",
	"PASS": "password"
}

CHECKS = {
	"icmp": {
		"timeout": 5
	}
}

TEAMS = {
	"MIN_NUM": 1,
	"MAX_NUM": 11,
}

SERVICES = {
	"Ubuntu Clients": _Service(
		"icmp",
		"check_icmp",
		_Data("IP", "10.%(team)d.1.10", edit=False),
		_Data("IP", "10.%(team)d.1.20", edit=False)
	),

	"Windows Clients": _Service(
		"icmp",
		"check_icmp",
		_Data("IP", "10.%(team)d.1.30", edit=False),
		_Data("IP", "10.%(team)d.1.40", edit=False)
	),

	# Active Directory
	"AD": _Service(
		"ldap",
		"check_ldap_lookup",
		_Data("HOST", "10.%(team)d.1.50", order=0),
		_Data("DOMAIN", "loribird%(team)d.win", edit=False, order=1),
		_Data("USERPASS", "jgeistBird||Changeme123!", order=2),
		_Data("USERPASS", "jdrosteBird||Changeme123!", order=2)
	),

	# Wordpress
	"HTTP Web": _Service(
		"http",
		"check_wordpress",
		_Data("HOST", "10.%(team)d.2.2", order=0),
		_Data("PORT", "80", order=1),
		_Data("USERPASS", "BirdMan||changeme", order=2),
	),

	# Squirrelmail
	"HTTP Mail": _Service(
		"http",
		"check_http",
		_Data("HOST", "10.%(team)d.2.4", order=0),
		_Data("PORT", "80", order=1)
	),

	"FTP": _Service(
		"ftp",
		"check_upload_download",
		_Data("HOST", "10.%(team)d.2.5", order=0),
		_Data("USERPASS", "bigbird||Lorirox123", order=1)
	),

	"IMAP": _Service(
		"imap",
		"check_imap_login",
		_Data("HOST", "10.%(team)d.2.4", order=0),
		_Data("PORT", "143", order=1),
		_Data("USERPASS", "backups||changeme", order=2)
	),

	# MySQL
	"DB": _Service(
		"mysql",
		"check_wordpress",
		_Data("HOST", "10.%(team)d.2.3", order=0),
		_Data("PORT", "3306", order=1),
		_Data("USER", "MariaBird", order=2),
		_Data("PASS", "lori4prez", order=3),
		_Data("DB_LOOKUP", "wordpress", order=4),
		_Data("BLOG_NAME", "Lori Bird 4 Prez 2k17", order=5)
	),
}
