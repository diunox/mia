from flask import Flask, render_template
import boto3
import os
import threading
import time
from flask import request

# ugly globals but this isn't MVC so I don't have a good way to share data across pages atm
minblock = ""
maxblock = ""
numfiles = ""
bucket = ""
application = Flask(__name__)


@application.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@application.route("/testing", methods=['POST'])
def testing():
    # Form variables
    global minblock
    global maxblock
    global numfiles
    global bucket

    minblock = request.form['minblock']
    maxblock = request.form['maxblock']
    numfiles = int(request.form['numfiles'])
    bucket = request.form['bucket']
    # timer storage
    time_to_upload = []

    for x in range(numfiles):
        command = "dd if=/dev/urandom of=/tmp/file.{} bs=$(shuf -i{}-{} -n1) count=1024".format(x, minblock, maxblock)
        os.system(command)

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=request.form['region'],
                            endpoint_url= request.form['endpoint'],
                            aws_access_key_id=request.form['accesskey'],
                            aws_secret_access_key=request.form['secretkey'])

    total_start = time.time()
    for x in range(numfiles):
        local_start = time.time()
        client.upload_file('/tmp/file.{}'.format(x),  # Path to local file
            bucket,  # Name of Space
            'file.{}'.format(x))  # Name for remote file
        local_end = time.time()
        local_time = local_end - local_start
        time_to_upload.append(local_time)

    total_end = time.time()
    total_time = total_end - total_start

    #cleanup logic goes here
    filedict = [{"Key": f"file.{n}"} for n in range(numfiles)]
    response = client.delete_objects(
        Bucket=bucket,
        Delete={
            'Objects': filedict,
            'Quiet': True
        },
    )

    mean = sum(time_to_upload) / int(numfiles)
    lowest = min(time_to_upload)
    highest = max(time_to_upload)

    # cleanup /tmp
    os.system("rm -f /tmp/*")
    return render_template("results.html", total_time=total_time, mean=mean, lowest=lowest, highest=highest)

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
