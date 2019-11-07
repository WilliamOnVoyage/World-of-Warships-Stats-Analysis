FROM python:3

WORKDIR wows
COPY . .
RUN python setup.py install

ENV PYTHONPATH=$PYTHONPATH:.

RUN pytest test
RUN coverage erase