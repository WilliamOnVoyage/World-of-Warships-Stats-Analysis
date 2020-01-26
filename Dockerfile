FROM python:3

ENV PYTHONPATH=$PYTHONPATH:/wows
WORKDIR /wows
COPY . .

RUN python setup.py install
