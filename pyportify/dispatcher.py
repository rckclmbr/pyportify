
import asyncio
import pkgutil
import sys

from aiohttp import web_urldispatcher as d, web, hdrs
from pathlib import Path

IS_BUNDLED = getattr(sys, 'frozen', False)


class StaticRoute(d.Route):

    def __init__(self, name, prefix, *,
                 expect_handler=None, chunk_size=256*1024):
        assert prefix.startswith('/'), prefix
        assert prefix.endswith('/'), prefix
        super().__init__(
            'GET', self.handle, name, expect_handler=expect_handler)
        self._prefix = prefix
        self._prefix_len = len(self._prefix)
        self._chunk_size = chunk_size

    def match(self, path):
        if not path.startswith(self._prefix):
            return None
        return {'filename': path[self._prefix_len:]}

    def url(self, *, filename, query=None):
        if isinstance(filename, Path):
            filename = str(filename)
        while filename.startswith('/'):
            filename = filename[1:]
        url = self._prefix + filename
        return self._append_query(url, query)

    def get_info(self):
        return {'prefix': self._prefix}

    @asyncio.coroutine
    def handle(self, request):
        filename = request.match_info['filename']
        ct, encoding = d.mimetypes.guess_type(str(filename))
        if not ct:
            ct = 'application/octet-stream'

        resp = web.Response()
        resp.content_type = ct
        if encoding:
            resp.headers[hdrs.CONTENT_ENCODING] = encoding

        data = pkgutil.get_data('pyportify', filename)
        if data is None:
            raise web.HTTPNotFound()
        resp.body = data
        resp.set_tcp_cork(True)
        return resp


def static_factory(url, directory):
    @asyncio.coroutine
    def static_view(request):
        url_path = request.match_info['url_path']
        route = get_static_route(url, directory)
        if url_path == '':
            url_path = 'index.html'
        request.match_info['filename'] = url_path
        ret = yield from route.handle(request)
        return ret
    return static_view


def get_static_route(url, directory):
    prefix = url.rsplit('/', 1)[0] or '/'
    if IS_BUNDLED:
        route = StaticRoute(None, prefix)
    else:
        route = web.StaticRoute(None, prefix, directory)
    return route
