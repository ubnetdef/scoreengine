def check_example(check, data):
	check.addOutput("ScoreEngine: %s Check\n" % (check.getServiceName()))
	check.addOutput("EXPECTED: Nothing")
	check.addOutput("OUTPUT: Nothing")

	check.setPassed()