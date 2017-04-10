import argparse
from celery.bin import worker as Worker

import config
from scoring import celery_app, engine
from scoring.master2 import Master


def main(args):
	if args.reset:
		engine.execute("TRUNCATE checks;")

	# ScoreEngine will automatically start at
	# round+1, so subtract 1 if we're given a round
	round = args.round
	if round > 0:
		round -= 1

	if args.worker:
		worker = Worker.worker(app=celery_app)
		worker.run(**config.CELERY["WORKER"])
	else:
		master = Master(round=round)
		master.run()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='ScoreEngine')

	parser.add_argument('--reset', help='reset all existing checks', action='store_true', default=False)
	parser.add_argument('--round', help='round to start at', type=int, default=0)

	group = parser.add_mutually_exclusive_group()
	group.add_argument('--master', help='only add tasks to the task queue', action='store_true')
	group.add_argument('--worker', help='only handle checks from the task queue', action='store_true')

	main(parser.parse_args())
