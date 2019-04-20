FROM python:3

WORKDIR .
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONPATH=$PYTHONPATH:.

CMD [ "python", "setup.py install" ]
CMD [ "coverage run --source wows_stats -m pytest" ]
CMD [ "python", "bin/collect-wows-data.py" ]