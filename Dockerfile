FROM python:3

WORKDIR .
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONPATH=$PYTHONPATH:.

CMD [ "python", "setup.py install" ]
CMD [ "python", "bin/collect-wows-data.py" ]