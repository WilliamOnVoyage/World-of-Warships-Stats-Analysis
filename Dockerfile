FROM python:3

WORKDIR .
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONPATH=$PYTHONPATH:.

#TODO: fix below run cmd
#RUN python setup.py install
RUN pytest test
RUN coverage erase
CMD ["python bin/collect-wows-ids.py -c config.json"]