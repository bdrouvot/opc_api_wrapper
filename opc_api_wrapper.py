# Author: Bertrand Drouvot
# Blog : http://bdrouvot.wordpress.com/
# opc_api_wrapper.py : V1.0 (2018/05)
# Oracle cloud API wrapper

from yaml import safe_load
import os
from os import path
import logging
import json
import requests
import time
from docopt import docopt

FORMAT = '%(asctime)s - %(name)s - %(levelname)-s %(message)s'

help = ''' Oracle Public Cloud Wrapper

Usage:
    opc_api_wrapper.py <service_name> create_instance

Options:
    -h  Help message

    Returns .....
'''

class APIError(Exception):

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = 415

    def to_dict(self):
        rv = dict()
        rv['message'] = self.message
        return rv

def launch_actions(kwargs):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        f = open('{0}/.oracleapi_config.yml'.format(dir_path), 'r')
        config = safe_load(f)
    except:
        raise ValueError("This script requires a .oracleapi_config.yml file")
        exit(-1)

    if kwargs['create_instance']:
        create_instance(kwargs['service_name'],dir_path,config)

def return_last_from_list(v_list):
    for msg in (v_list[0], v_list[-1]):
        pass
    return msg

def print_all_from_list(v_list):
    for mmsg in v_list:
        print mmsg

def check_job(config,joburl):

    IDENTITY_DOMAIN_ID = config['identityDomainId']
    USERNAME = config['username']
    PASSWORD = config['password']

    client = requests.Session()
    client.auth = (USERNAME, PASSWORD)
    client.headers.update({'X-ID-TENANT-NAME': '{0}'.format(IDENTITY_DOMAIN_ID)})

    response = client.get("{0}".format(joburl))
    jsontext= json.loads(response.text)
    client.close()
    return (jsontext['job_status'],jsontext['message'])


def create_instance(service_name,dir_path,config):

    logfile = config['logfile']
    logging.basicConfig(filename=logfile, format=FORMAT, level=logging.INFO)

    IDENTITY_DOMAIN_ID = config['identityDomainId']
    USERNAME = config['username']
    PASSWORD = config['password']

    data = json.load(open('{0}/prov_database.json'.format(dir_path), 'r'))
    data['serviceName'] = service_name

    print "creating opc instance {0}...".format(service_name)

    client = requests.Session()
    client.auth = (USERNAME, PASSWORD)
    client.headers.update(
        {'content-type': 'application/json',
         'X-ID-TENANT-NAME':'{0}'.format(IDENTITY_DOMAIN_ID)})

    response = client.post("https://dbcs.emea.oraclecloud.com/paas/service/dbcs/api/v1.1/instances/{0}".format(IDENTITY_DOMAIN_ID), json=data)
    if response.status_code != 202:
        raise APIError(response.json()['message'])
    jobburl = response.headers['Location']
    jobsstatus = "InProgress"
    while (jobsstatus == "InProgress"):
        time.sleep(120)
        jobsstatus,jobmessage = check_job(config,jobburl)
        print "{0} ({1})".format(jobsstatus,return_last_from_list(jobmessage))
    client.close()
    print ""
    print "opc instance {0} created:".format(service_name)
    print ""
    print_all_from_list(jobmessage)

#
# Main
#

def main():

    arguments = docopt(help)
    for key in arguments.keys():
        arguments[key.replace('<','').replace('>','')] = arguments.pop(key)

    launch_actions(arguments)

if __name__ == '__main__':
    main()
