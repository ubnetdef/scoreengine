import subprocess
from config import config

# DEFAULTS
imcp_config = {
	'timeout': 5,
	'command': "ping"
}
# /DEFAULTS

# CONFIG
if "imcp" in config:
	imcp_config.update(config["imcp"])
# /CONFIG

def check_imcp(check, data):
	command = [imcp_config["command"], "-c", "1", "-t", str(imcp_config["timeout"]), str(data["IP"])]
	strCommand = ' '.join(command)

	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("RUNNING: %s" % (strCommand))
	check.addOutput("EXPECTED: 1 packet received")
	check.addOutput("OUTPUT:")

	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(output, stderr) = proc.communicate()

	check.addOutput(output)

	if proc.returncode is 0:
		check.setPassed()
