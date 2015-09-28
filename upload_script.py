#!/usr/bin/env python

import json, urllib2
from argparse import ArgumentParser
import os
from xml_dict import *

FILE_MAP = [
            ('cookie_persistence_map' ,'/xml_objects/PERSISTs-COOKIE.txt'),
            ('src_ip_persistence_map' ,'/xml_objects/PERSISTs-SRC_IP.txt'),
            ('ssl_id_persistence_map' ,'/xml_objects/PERSISTs-SSL_ID.txt'),
            ('real_server_map'        ,'/xml_objects/RSs.txt'),
            ('service_group_map'      ,'/xml_objects/SGs.txt'),
            ('vip_map'                ,'/xml_objects/VIPs.txt'),               
           ]

TEXT_MAP  = {
             'cookie_persistence_template_list' : 'COOKIE PERSISTENCE',
             'src_ip_persistence_template_list' : 'SOURCE IP PERSISTENCE',
             'ssl_sid_persist_template_list'    : 'SSL ID PERSISTENCE',
             'server_list'                      : 'REAL SERVER',
             'service_group_list'               : 'SERVICE GROUP',
             'virtual_server_list'              : 'VIRTUAL SERVER',               
            }

METHOD_MAP = {
              'cookie_persistence_map' : 'slb.template.cookie_persistence.create',
              'src_ip_persistence_map' : 'slb.template.src_ip_persistence.create',
              'ssl_id_persistence_map' : 'slb.template.ssl_sid_persistence.create',  
              'real_server_map'        : 'slb.server.create',
              'service_group_map'      : 'slb.service_group.create',
              'vip_map'                : 'slb.virtual_server.create',               
             }

FILTER_MAP = {
             'cookie_persistence_template_list' : 'name=',
             'src_ip_persistence_template_list' : 'name=',
             'ssl_sid_persist_template_list'    : 'name=',
			  'server_list'						: 'server=name',
			  'service_group_list'				: 'service_group=name',
			  'virtual_server_list' 			: 'virtual_server=name',
			 }

class A10Device_XML(object):
    '''
    Class to abstract aXAPI session creation and method calling using HTTPs POST Requests
    and Responses.
    '''

    def __init__(self, ip, username, password, debug=False):
        self.ip= ip
        self.username = username
        self.password = password
        self.debug = debug
    def getSession(self):        
        url = "http://" + self.ip + "/services/rest/V2.1/?method=authenticate&format=url&username=" + self.username + "&password=" + self.password
        if self.debug: print "Generated URL: " + url
        rsp = urllib2.urlopen(url)
        content = rsp.read()
        if self.debug: print "Result: " + content
        data = ConvertXmlToDict(content)['response']
        # A library to parse the returned XML object to a python dictionary is required
        # to extract the session_id from the response
        self.session_id = data['session_id']
        print "Session Created. Session ID: " + self.session_id
    def closeSession(self):
        if self.debug: print "Closing Session: "+ self.session_id
        url = "http://" + self.ip + "/services/rest/V2.1/?session_id=" + self.session_id + "&format=url&method=session.close"
        if self.debug: print "Generated URL: " + url
        rsp = urllib2.urlopen(url)
        content = rsp.read()
        print "Result: " + content
    def genericPostApi(self,slb_data):
        url = "http://"+self.ip+"/services/rest/V2.1/?session_id=" + self.session_id + "&format=url&method="+ self.method + slb_data
        if self.debug: print "Generated URL: " + url
        rsp = urllib2.urlopen(url)
        content = rsp.read()
        print (content)
    def setMethod(self, method):
    	self.method = method
        
def main():
    '''
    Loads all the files existing in FILE_MAP. Then calls the aXAPI methods defined in 
    METHOD_MAP to upload the configuration to the A10 box. This is done by a loop that 
    loads a file (which contains alls the instances of a configuration element) and uses
    the particular aXAPI method to upload all the instances of that element.
    '''
    # Argument parsing
    script_name = os.path.basename(__file__)
    parser = ArgumentParser(description=("Script to load the alteon processed "
                            "configuration file and upload it to the A10 box"), 
                            prog='python ' + script_name)
    parser.add_argument('a10_ip_address', action='store', help='A10 management IP')
    parser.add_argument('a10_admin_user', action='store', help='A10 admin user',
                        default='admin', nargs='?',) # Optional arg, defaults to 'admin'
    parser.add_argument('a10_admin_pwd', action='store', help='A10 admin user password',
                        default='a10', nargs='?',)   # Optional arg, defaults to 'a10'
    parser.add_argument('-v', '--verbose', action='store_true', help=('increase output '
                        'verbosity showing HTTPs POST Requests/Responses in detail'), 
                        dest= 'verbose')                    
    parsed_args = parser.parse_args()

    ip_address = parsed_args.a10_ip_address
    username = parsed_args.a10_admin_user
    password = parsed_args.a10_admin_pwd
    verbose = parsed_args.verbose
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Initialize with IP, username, password and debugging for the instance
    thunder = A10Device_XML(ip_address, username, password, True)
    thunder.getSession()                                # GET authentication session
 
    for (a_map, file_to_process) in FILE_MAP:
    
    	thunder.setMethod(METHOD_MAP[a_map])              # SET Method
    	
    	with open(script_dir + file_to_process, 'r') as a_file:
        	a_string = a_file.read()
    	a_file.close()
    	
    	# Remove '\n' from file content
    	a_string_list = a_string.split('\n')
    	a_string = ''.join(a_string_list)
    	
    	# All the files are strings with a initial keyword that indicates to FILTER_MAP
    	# the string delimiter. Variable 'a_filter_string' is the delimiter used to build
    	# the query string to be added to the URL.
    	(trash, value, a_string) = a_string.split('&', 2)
 
    	# Get the delimiter and format the string
    	a_filter_string = '&' + FILTER_MAP[value]
    	a_string = '&' + a_string
 
 
 		# Get a list without the filter string at the end of each element   	
    	a_element_list = a_string.split(a_filter_string)
    	a_element_list.pop(0)
    	
    	for index, a_query_string in enumerate(a_element_list):
    		print "### Uploading {} {} CONFIGURATION ###".format(TEXT_MAP[value], 
    		                                                     str(index+1))
    		
    		# Call API to execute the method. Here we append the delimiter substring we
    		# removed during the split stage to get the list
        	thunder.genericPostApi(a_filter_string + a_query_string)
    
    	print
 
    
    thunder.closeSession()                          # Close Session
    
    

if __name__ == '__main__':
    main()
    
    