#!/usr/bin/env python
import logging
import sys

from pyportify.views import app as application
from gevent import monkey
from socketio.server import SocketIOServer

monkey.patch_all()


def main():
    print "Open your browser and go to http://localhost:3132"

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    application.logger.addHandler(ch)

    SocketIOServer(
        ('', application.config['PORT']),
        application,
        resource="socket.io").serve_forever()


if __name__ == '__main__':
    main()
