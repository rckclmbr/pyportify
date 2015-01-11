#!/usr/bin/env python

from pyportify.wsgi import application
import cherrypy


def main():
    cherrypy.tree.graft(application, "/")
    cherrypy.server.unsubscribe()
    server = cherrypy._cpserver.Server()

    server.socket_host = "0.0.0.0"
    server.socket_port = 3132
    server.thread_pool = 10

    server.subscribe()

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
