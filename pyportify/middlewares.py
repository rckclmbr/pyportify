import asyncio


def IndexMiddleware(index='index.html'):
    @asyncio.coroutine
    def middleware_factory(app, handler):
        @asyncio.coroutine
        def index_handler(request):
            try:
                filename = request.match_info['filename']
                if not filename:
                    filename = index
                if filename.endswith('/'):
                    filename += index
                request.match_info['filename'] = filename
            except KeyError:
                pass
            ret = yield from handler(request)
            return ret
        return index_handler
    return middleware_factory
