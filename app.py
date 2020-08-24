from flask import Flask, render_template
import boto3
import os
import threading
import time
from flask import request

# ugly globals but this isn't MVC so I don't have a good way to share data across pages atm
numfiles = ""
bucket = ""
region = ""
endpoint = ""
accesskey = ""
secretkey = ""
postresults = {}

application = Flask(__name__)


@application.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@application.route("/post-testing", methods=['POST'])
def posttesting():

    # Form variables
    global numfiles
    global bucket
    global region
    global endpoint
    global accesskey
    global secretkey
    global postresults

    minblock = request.form['minblock']
    maxblock = request.form['maxblock']
    numfiles = int(request.form['numfiles'])
    bucket = request.form['bucket']
    region = request.form['region']
    endpoint = request.form['endpoint']
    accesskey = request.form['accesskey']
    secretkey = request.form['secretkey']

    # timer storage
    time_to_upload = []

    try:
        for x in range(numfiles):
            command = "dd if=/dev/urandom of=/tmp/file.{} bs=$(shuf -i{}-{} -n1) count=1024".format(x, minblock, maxblock)
            os.system(command)

    except Exception as error:
        message = "Error generating objects, details potentially below:"
        return render_template("error.html", error=error)
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                                region_name=region,
                                endpoint_url= endpoint,
                                aws_access_key_id=accesskey,
                                aws_secret_access_key=secretkey)
    except Exception as error:
        message = "Error initializing session, details potentially below:"
        return render_template("error.html", error=error)

    try:
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
    except Exception as error:
        message = "Error occurred during upload, details potentially below:"
        return render_template("error.html", error=error)
    # cleanup /tmp
    os.system("rm -f /tmp/file.*")

    mean = sum(time_to_upload) / int(numfiles)
    lowest = min(time_to_upload)
    highest = max(time_to_upload)

    postresults['total'] = total_time
    postresults['mean'] = mean
    postresults['lowest'] = lowest
    postresults['highest'] = highest

    return render_template("partial-results.html", total_time=total_time, mean=mean, lowest=lowest, highest=highest)


@application.route("/get-testing", methods=['GET'])
def gettesting():
    global numfiles
    global bucket
    global region
    global endpoint
    global accesskey
    global secretkey
    global postresults

    print("about to start uploads")

    # timer storage
    time_to_download = []

    try:
        session = boto3.session.Session()
        client = session.client('s3',
                                region_name=region,
                                endpoint_url=endpoint,
                                aws_access_key_id=accesskey,
                                aws_secret_access_key=secretkey)
    except Exception as error:
        message = "Error initializing session, details potentially below:"
        return render_template("error.html", error=error)

    total_start = time.time()
    for x in range(numfiles):
        local_start = time.time()
        client.download_file(bucket,  # Name of Space
            'file.{}'.format(x),  # Name for remote file
            '/tmp/file.{}'.format(x))  # Name and path for local file

        local_end = time.time()
        local_time = local_end - local_start
        time_to_download.append(local_time)

    total_end = time.time()
    total_time = total_end - total_start

    # cleanup /tmp
    os.system("rm -f /tmp/file.*")

    mean = sum(time_to_download) / int(numfiles)
    lowest = min(time_to_download)
    highest = max(time_to_download)


    # cleanup logic goes here
    filedict = [{"Key": f"file.{n}"} for n in range(numfiles)]
    response = client.delete_objects(
        Bucket=bucket,
        Delete={
            'Objects': filedict,
            'Quiet': True
        },
    )
    
    return render_template("results.html", post_total_time=postresults['total'],
                           post_mean=postresults['mean'], 
                           post_lowest=postresults['lowest'], 
                           post_highest=postresults['highest'],
                           get_total_time=total_time,
                           get_mean=mean,
                           get_lowest=lowest,
                           get_highest=highest
                           )


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
