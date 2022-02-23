#!/usr/bin/python3

import configparser
import socket
import requests
import json
import urllib3
import logging
from dns import resolver

# Diable warning ssl & add verify=False to all request.get
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read and Parse the confg file
config = configparser.ConfigParser()
config.read('/set/your/path/here/ddns.ini')

#config loggin
logging.basicConfig(filename=config['local']['logginfFilePath'], filemode='a', datefmt='%m/%d/%Y %I:%M:%S %p', format='%(asctime)s - %(levelname)s - %(message)s')


# API Endpoint for cPanel API2
URL = config['cpanel']['server'] + config['cpanel']['api']

DOMAIN = config['domain']['domain']
SUBDOMAIN = config['domain']['subdomain']

# What is my current actual IP address
MYIP = json.loads(requests.get("https://httpbin.org/ip").text)['origin']

# What is the IP address currently set in DNS
res = resolver.Resolver()
res.nameservers = ['8.8.8.8']
answers = res.resolve(DOMAIN)
for rdata in answers:
    DNSIP = rdata.address

#DNSIP = #socket.gethostbyname(DOMAIN)
#print(DNSIP)

# If they don't match then update DNS via the cPanel API
if MYIP != DNSIP:
    #logging.warning('IP si changed form: ' + DNSIP  + ' to: ' + MYIP )
    authparams = (
        config['cpanel']['username'],
        config['cpanel']['password']
    )

    # Call ZoneEdit::fetchzone to get the full zone file for DOMAIN
    fetchparams = (
        ('api.version', '2'),
        ('cpanel_jsonapi_module', 'ZoneEdit'),
        ('cpanel_jsonapi_func', 'fetchzone'),
        ('domain', DOMAIN),
    )

    response = requests.get(URL, auth=authparams, params=fetchparams, verify=False)
    zonefile = json.loads(response.text)

    # Read each record looking for the sub domain we want to update
    for i, r in enumerate(zonefile['cpanelresult']['data'][0]['record']):
        if 'name' in list(r) and r['name'] == DOMAIN+"." and r['type']=='A':
                if r['address'] != MYIP:
                   logging.warning('IP si changed form: ' + DNSIP  + ' to: ' + MYIP )
                   editparams = (
                   ('api.version', '2'),
                   ('cpanel_jsonapi_module', 'ZoneEdit'),
                   ('cpanel_jsonapi_func', 'edit_zone_record'),
                   ('domain', DOMAIN),
                   ('line', r['line']),
                   ('name', r['name']),
                   ('type', r['type']),
                   ('address', MYIP),
                   )

                   response = requests.get(URL, auth=authparams, params=editparams, verify=False)
                #else:
                   #logging.warning('IP no changed yet' )
