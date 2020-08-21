from flask import Flask, render_template
import boto3
import os
import threading
import time
from flask import request

POOL_TIME = 5 #Seconds

# variables that are accessible from anywhere
commonDataStruct = {}
# lock to control access to variable
dataLock = threading.Lock()
# thread handler
yourThread = threading.Thread()

application = Flask(__name__)


@application.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@application.route("/testing", methods=['POST'])
def testing():
    # Form variables
    minblock = request.form['minblock']
    maxblock = request.form['maxblock']
    numfiles = request.form['numfiles']

    # timer storage
    time_to_upload = []

    for x in range(int(numfiles)):
        command = "dd if=/dev/urandom of=/tmp/file.{} bs=$(shuf -i{}-{} -n1) count=1024".format(x, minblock, maxblock)
        os.system(command)

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=request.form['region'],
                            endpoint_url='https://%s.digitaloceanspaces.com' % (request.form['region']),
                            aws_access_key_id=request.form['accesskey'],
                            aws_secret_access_key=request.form['secretkey'])

    total_start = time.time()
    for x in range(int(numfiles)):
        local_start = time.time()
        client.upload_file('/tmp/file.{}'.format(x),  # Path to local file
            request.form['bucket'],  # Name of Space
            'file.{}'.format(x))  # Name for remote file
        local_end = time.time()
        local_time = local_end - local_start
        time_to_upload.append(local_time)

    total_end = time.time()
    total_time = total_end - total_start

    mean = sum(time_to_upload) / numfiles
    lowest = min(time_to_upload)
    highest = max(time_to_upload)

    return render_template("results.html", total_time=total_time, mean=mean, lowest=lowest, highest=highest)


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
