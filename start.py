import argparse
from scoring import engine
from scoring.master import Master

def main(args):
	if args.reset:
		engine.execute("TRUNCATE checks;")

	# ScoreEngine will automatically start at
	# round+1, so subtract 1 if we're given a round
	round = args.round
	if round > 0:
		round -= 1

	master = Master(round=round)
	master.run()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='ScoreEngine')

	parser.add_argument('--reset', help='reset all existing checks', action='store_true', default=False)
	parser.add_argument('--round', help='round to start at', type=int, default=0)

	main(parser.parse_args())