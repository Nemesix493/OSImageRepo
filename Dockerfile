FROM python:3.11

COPY . /workspace/

WORKDIR /workspace

RUN pip install -r requirements.txt

CMD [ "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "api:app" ]