import logging
import sys


# Create a logger and assign it a name, can be a string eg. myapp
logger = logging.getLogger(__name__)

# Format the messages with a time, etc.
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Send all messages to standard output
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

# Capture ERROR and higher to a log file
file_handler = logging.FileHandler('myapp.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# Test, all messages go to stdout while <= ERROR are captured to the log file too.
logger.debug('debug message')
logger.info('info message')
logger.warning('warn message')
logger.error('error message')
logger.critical('critical message')
