FROM ubuntu:14.04

MAINTAINER Josh Braegger <rckclmbr@gmail.com>

RUN apt-get update && apt-get install -y curl
RUN curl -s https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -; \
    curl -s https://apt.mopidy.com/mopidy.list > /etc/apt/sources.list.d/mopidy.list; \
    apt-get update

RUN apt-get install -y python-pip python-dev libffi-dev libspotify-dev
RUN pip install virtualenv && virtualenv --system-site-packages /ve

ADD . /app/
RUN touch /app/README.rst
RUN /ve/bin/pip install -r /app/requirements.txt
RUN /ve/bin/pip install /app/

EXPOSE 3132
CMD ["/ve/bin/pyportify"]
