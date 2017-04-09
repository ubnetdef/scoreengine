def check_example(check, data):
	check.addOutput("ScoreEngine: {} Check\n".format(check.getServiceName()))
	check.addOutput("EXPECTED: Nothing")
	check.addOutput("OUTPUT: Nothing")

	check.setPassed()