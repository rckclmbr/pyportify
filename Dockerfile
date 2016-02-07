FROM ubuntu:15.04

MAINTAINER Josh Braegger <rckclmbr@gmail.com>

RUN apt-get update 
RUN apt-get install -y python3 python3-pip git
RUN pip3 install virtualenv && virtualenv -p python3 /ve

ADD . /app/
RUN touch /app/README.rst
RUN /ve/bin/pip install -r /app/requirements.txt
RUN /ve/bin/pip install /app/

EXPOSE 3132
CMD ["/ve/bin/pyportify"]
