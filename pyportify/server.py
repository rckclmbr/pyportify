#!/usr/bin/env python
from pyportify.views import app as application
from gevent import monkey
from socketio.server import SocketIOServer

monkey.patch_all()


def main():
    print "Open your browser and go to http://localhost:3132"
    SocketIOServer(
        ('', application.config['PORT']),
        application,
        resource="socket.io").serve_forever()


if __name__ == '__main__':
    main()
