import argparse
import config
from celery.bin import worker as Worker
from scoring import celery_app, engine

def main(args):
	if args.reset:
		engine.execute("TRUNCATE checks; TRUNCATE rounds; TRUNCATE celery_taskmeta;")


	round = args.round
	if args.resume:
		lastRound = engine.execute("SELECT MAX(number) FROM rounds").first()
		round = lastRound[0] + 1

	# ScoreEngine will automatically start at
	# round+1, so subtract 1 if we're given a round
	if round > 0:
		round -= 1

	if args.worker:
		celery_app.autodiscover_tasks(['scoring.worker'])

		worker = Worker.worker(app=celery_app)
		worker.run(**config.CELERY["WORKER"])
	else:
		if args.queue:
			from scoring.masters.queue import QueueMaster as Master
		else:
			from scoring.masters.thread import ThreadMaster as Master
		
		master = Master(round=round)
		master.run()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='ScoreEngine control center')

	group_round = parser.add_mutually_exclusive_group()
	group_round.add_argument('--round', help='round to start at', type=int, default=0)
	group_round.add_argument('--resume', help='start with the highest finished round', action='store_true', default=False)
	group_round.add_argument('--reset', help='reset all existing checks', action='store_true', default=False)

	group_type = parser.add_mutually_exclusive_group(required=True)
	group_type.add_argument('--thread', help='use the thread master for running tasks', action='store_true')
	group_type.add_argument('--queue', help='use the queue master for running tasks', action='store_true')
	group_type.add_argument('--worker', help='launch a queue worker for handling tasks', action='store_true')

	main(parser.parse_args())
