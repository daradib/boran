FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code && mkdir /code/data
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
