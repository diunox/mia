FROM python:3.6
ADD . /app
WORKDIR /app
RUN pip install flask gunicorn boto3 psycopg2-binary flask-sqlalchemy
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:80", "-t", "300", "app"]
