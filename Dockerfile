FROM python:3-alpine

MAINTAINER Josh Braegger <rckclmbr@gmail.com>

ADD . /app/
RUN pip install -r /app/requirements.txt && \
    pip install /app && \
    rm -r /root/.cache

EXPOSE 3132
CMD ["/usr/local/bin/pyportify"]

