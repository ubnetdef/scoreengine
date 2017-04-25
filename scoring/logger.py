import config
import logging
import logging.config

# Setup logging
logging.config.dictConfig(config.LOGGING)

# Create our loggers
logger = logging.getLogger("scoreengine")
round_logger = logging.getLogger("scoreengine.round")
traffic_logger = logging.getLogger("scoreengine.traffic")
reaper_logger = logging.getLogger("scoreengine.reaper")
