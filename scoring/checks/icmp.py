import subprocess
import config

# DEFAULTS
icmp_config = {
	'timeout': 10,
	'command': "ping"
}
# /DEFAULTS

# CONFIG
if "icmp" in config.CHECKS:
	icmp_config.update(config.CHECKS["icmp"])
# /CONFIG

def check_icmp(check, data):
	command = [icmp_config["command"], "-c", "1", "-t", str(icmp_config["timeout"]), str(data["IP"])]
	strCommand = ' '.join(command)

	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("RUNNING: {}".format(strCommand))
	check.addOutput("EXPECTED: 1 packet received")
	check.addOutput("OUTPUT:")

	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(output, stderr) = proc.communicate()

	check.addOutput(output)

	if proc.returncode is 0:
		check.setPassed()
