import os
import boto3
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from multiprocessing.dummy import Pool


def data_to_s3(frmt):
    # throws error occured if there was a problem accessing data
    # otherwise downloads and uploads to s3

    source_dataset_url = 'https://data.cms.gov/api/views/qcn7-gc3g/rows'

    try:
        response = urlopen(source_dataset_url + frmt)

    except HTTPError as e:
        raise Exception('HTTPError: ', e.code, frmt)

    except URLError as e:
        raise Exception('URLError: ', e.reason, frmt)

    else:
        data_set_name = os.environ['DATASET_NAME']
        filename = data_set_name + frmt
        file_location = '/tmp/' + filename

        with open(file_location, 'wb') as f:
            f.write(response.read())
            f.close()

        # variables/resources used to upload to s3
        s3_bucket = os.environ['ASSET_BUCKET']
        new_s3_key = data_set_name + '/dataset/'
        s3 = boto3.client('s3')

        s3.upload_file(file_location, s3_bucket, new_s3_key + filename)

        print('Uploaded: ' + filename)

        # deletes to preserve limited space in aws lamdba
        os.remove(file_location)

        # dicts to be used to add assets to the dataset revision
        return {'Bucket': s3_bucket, 'Key': new_s3_key + filename}


def source_dataset():

    # list of enpoints to be used to access data included with product
    data_endpoints = [
        '.json',
        '.csv'
    ]

    # multithreading speed up accessing data, making lambda run quicker
    with (Pool(2)) as p:
        asset_list = p.map(data_to_s3, data_endpoints)

    # asset_list is returned to be used in lamdba_handler function
    return asset_list
