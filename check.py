from __future__ import print_function
import argparse
from scoring import Session
from scoring.master import Master
from scoring.models import Team, Service
import sys

def main(args):
	session = Session()
	teamDB = session.query(Team).filter(Team.id == args.team).first()

	if not teamDB:
		print("ERROR: Unknown Team ID")
		sys.exit(1)

	print("> Team: %s" % (teamDB.name))
	team = {
		'id': teamDB.id,
		'name': teamDB.name
	}

	serviceDB = session.query(Service).filter(Service.id == args.service).first()

	if not serviceDB:
		print("ERROR: Unknown Service ID")
		sys.exit(1)

	print("> Service: %s" % (serviceDB.name))
	service = {
		'id': serviceDB.id,
		'name': serviceDB.name,
		'group': serviceDB.group,
		'check': serviceDB.check
	}

	master = Master()
	master.new_check(team, service, 0, dryRun=True)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='ScoreEngine Simple Check')

	parser.add_argument('team', type=int,help='team id')
	parser.add_argument('service', type=int, help='service id')

	main(parser.parse_args())