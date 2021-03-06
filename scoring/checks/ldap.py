from __future__ import absolute_import
import config
import ldap


# DEFAULTS
ldap_config = {
	'timeout': 15,
}
# /DEFAULTS

# CONFIG
if "ldap" in config.CHECKS:
	ldap_config.update(config.CHECKS["ldap"])
# /CONFIG

def check_ldap_lookup(check, data):
	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful and correct query against the AD (LDAP) server")
	check.addOutput("OUTPUT:\n")

	check.addOutput("Starting check...")

	try:
		# Setup LDAP
		l = ldap.initialize('ldap://{HOST}'.format(**data))

		# Bind to the user we're using to lookup
		actual_username = "{USER}@{DOMAIN}".format(**data)
		password = data["PASS"]

		l.protocol_version = ldap.VERSION3
		l.set_option(ldap.OPT_NETWORK_TIMEOUT, ldap_config["timeout"])
		l.simple_bind_s(actual_username, password)

		# We're good!
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: {}: {}".format(type(e).__name__, e))

		return
