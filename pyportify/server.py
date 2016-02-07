#!/usr/bin/env python3

import asyncio
from pyportify import app


def main():
    loop = asyncio.get_event_loop()
    handler = loop.run_until_complete(app.setup(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(handler.finish_connections())
        loop.close()

if __name__ == "__main__":
    main()
