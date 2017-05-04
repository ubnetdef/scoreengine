import config
import logging
import logging.config

# Setup logging
logging.config.dictConfig(config.LOGGING)

# Create our loggers
main = logging.getLogger("scoreengine")
round = logging.getLogger("scoreengine.round")
traffic = logging.getLogger("scoreengine.traffic")
reaper = logging.getLogger("scoreengine.reaper")
worker = logging.getLogger("scoreengine.worker")