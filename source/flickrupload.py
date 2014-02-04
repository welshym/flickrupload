__author__ = "Khosrow Ebrahimpour <khosrow.ebrahimpour@gmail.com>"
__version__ = "$Rev: 3 $"
__date__ = "$Date: 2010-10-31 19:05:46 +0400 (Sun, 31 Oct 2010) $"
__copyright__ = "Copyright 2010 Khosorw Ebrahimpour"


import httplib
import mimetypes
import flickr
from xml.dom import minidom
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2             
import hashlib
             
#def upload(self, filename, **params):    NOTE: No need to include the self parameter
def upload(filename, **params):
        sig = flickr._get_api_sig(params=params)
        # Register the streaming http handlers with urllib2
        register_openers()
        
        params['api_key'] = flickr.API_KEY
        params['auth_token'] = flickr.userToken()        
        params['api_sig'] = sig        
        params['photo'] = open(filename, 'rb')
        
        datagen, headers = multipart_encode(params)

        url = "http://up.flickr.com" + "/services/upload/"        
        # Create the Request object
        request = urllib2.Request(url, datagen, headers)
        # Actually do the request, and get the response
        response = urllib2.urlopen(request).read()
        # use get data since error checking is handled by it already
        data = flickr._get_data(minidom.parseString(response))
        photo = flickr.Photo(data.rsp.photoid.text)
                
        return photo


"""
Code for post_multipart, encode_multipart_formdata, and get_content_type taken from
http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
PSF Licensed code
"""

import requests

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    print "host + selector", host + selector
    parameters = {'api_sig' : fields['api_sig'], 'auth_token' : fields['auth_token'], 'api_key' : fields['api_key'], 'title' : fields['title']}
    r = requests.post("http://" + host + selector, params=parameters, files=files, verify=False)
    return r

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """

    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields.items():
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)

        
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body
       
def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    
if __name__ == '__main__':
        # the code below is an example of how to do an upload
        # please use it as a guide only
        photo = upload(filename='image.jpg', title='some photo', tags='tag1 tag2', description='A test photo')  

        print "your photo is now at : %s" % photo.getURL()

         
    