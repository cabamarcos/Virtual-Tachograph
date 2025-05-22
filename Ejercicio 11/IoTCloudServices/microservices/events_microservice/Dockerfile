FROM python:3.12

WORKDIR /etc/usr/src/app

COPY ./code /etc/usr/src/app

COPY ./code/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "events_manager_api.py"]
