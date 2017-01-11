import sys
import logging


class Logger(object):
    """Replace stderr by logging message, and printing to stdout
    """
    def __init__(self):
        self.logger = logging.getLogger('fstimer')
        self.linebuf = ''
        
    def write(self, message):
        for line in message.strip().splitlines():
            self.logger.debug(line.strip())
        sys.stdout.write(message)


logger = logging.getLogger('fstimer')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('log.txt')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug('-----------Startup')

sys.stderr = Logger()
