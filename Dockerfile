FROM python:3.6
ADD . /app
WORKDIR /app
RUN pip install flask gunicorn boto3
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-t", "300", "app"]
