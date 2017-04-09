from __future__ import absolute_import
import config
from dns.resolver import Resolver

# DEFAULTS
dns_config = {
	'timeout': 5.0,
	'lifetime': 5.0
}
# /DEFAULTS

# CONFIG
if "dns" in config.CHECKS:
	dns_config.update(config.CHECKS["dns"])
# /CONFIG

def check_dns(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Sucessful and correct query against the DNS server")
	check.addOutput("OUTPUT:\n")

	# Setup the resolver
	resolv = Resolver()
	resolv.nameservers = [data["HOST"]]
	resolv.timeout = dns_config["timeout"]
	resolv.lifetime = dns_config["lifetime"]

	check.addOutput("Starting check...")

	try:
		# Query resolver
		check.addOutput("Querying %s for '%s'..." % (data["HOST"], data["LOOKUP"]))
		lookup = resolv.query(data["LOOKUP"], data["TYPE"])

		found = False
		for ans in lookup:
			if str(ans) == data["EXPECTED"]:
				found = True
			else:
				check.addOutput("NOTICE: DNS Server returned %" % (ans))

		if not found:
			check.addOutput("ERROR: DNS Server did not respond with the correct IP")
			return

		# We're good!
		check.setPassed()
		check.addOutput("Check successful!")
	except Exception as e:
		check.addOutput("ERROR: %s: %s" % (type(e).__name__, e))

		return
