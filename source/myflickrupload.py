"""
#!/usr/bin/env python

Created on Sep 29, 2011

@author: Mark Welsh
"""

__author__  = 'Mark Welsh'
__date__    = '2011-09-29'
__version__ = '0.1.0'
__rights__  = 'Copyright (c) 2011 Mark Welsh.'

class FlickrError(Exception): pass

import myflickrinfo
import os
import flickr
import flickrupload
import webbrowser
import sys
from cStringIO import StringIO
import argparse
import time
import urllib
import urllib2
import requests

def myAuthorization(myAuth=flickr.Auth()):
    # Dont use an authorized access for this attempt
    flickr.AUTH=False;
    permission = "write"
    try:
        frob = myAuth.getFrob()
    except IOError:
        print "Flickr Authentication Error: Frob"
        exit()
    
    link = myAuth.loginLink(permission, frob)
    browser = webbrowser.get()
    browser.open(link)
    
    print "Enable authorization through the Web Browser. Hit enter once complete."
    raw_input()
    
    # Get and store the token
    try:
        token = myAuth.getToken(frob)
    except IOError:
        print "Flickr Authentication Error: Token"
        exit()

    f = file('token.txt','w')
    f.write(token)
    f.close()
    
    # Now use authorized access for all subsequent updates
    flickr.AUTH=True;
    return



class Photo(object):
    """Represents a Flickr Photo."""

    def __init__(self, id, title, fullname):
        self.__id = id
        self.__title = title
        self.__fullname = fullname
        
    id = property(lambda self: self.__id)
    title = property(lambda self: self.__title)
    fullname = property(lambda self: self.__fullname)

    def __len__(self):
        return self.__count

    def __str__(self):
        return '<Flickr Photoset %s>' % self.id

class LocalPhotoset(object):
    def __init__(self, id, title, fullname):
        self.__id = id
        self.__title = title
        self.__fullname = fullname
        
    id = property(lambda self: self.__id)
    title = property(lambda self: self.__title)
    fullname = property(lambda self: self.__fullname)

    def __len__(self):
        return self.__count

    def __str__(self):
        return '<Flickr Photoset %s>' % self.id

    def getPhotos(self, enteredset=None, root=""):
        """Returns list of Photos."""                
 
        if enteredset is None:
            enteredset = []
        
        # Create the full path from the possibly recursive root variable passed in, this extends the set's root path
        fullpath = os.path.join(self.fullname, root)
        folder_content = os.listdir(fullpath)                
        i = 0;
        for photo in folder_content:
            #fullname = fullpath + "\\" + photo.lower()
#            fullname = os.path.join(fullpath, photo.lower())   
            fullname = os.path.join(fullpath, photo)               
            if os.path.isfile(fullname):
                if photo.lower().endswith("jpg"):
                    # Get rid of any slashes in the root path variable and concatonate the string name
#                    shortname = root.replace("\\", "") + photo.lower().strip(".jpg")                    
                    shortname = root.replace("\\", "") + photo.strip(".jpg")                    
                    enteredset.append(Photo(i, shortname, fullname))
                elif photo.endswith("JPG"):
                    # Get rid of any slashes in the root path variable and concatonate the string name
#                    shortname = root.replace("\\", "") + photo.lower().strip(".JPG")                    
                    shortname = root.replace("\\", "") + photo.strip(".JPG")                    
                    enteredset.append(Photo(i, shortname, fullname))
            else:
                # If the set path is real and not the misc path added for root pictures then recursively add photos
                if self.fullname.endswith(self.title):
                    # Extend the path and recursively search the folder
                    enteredset = self.getPhotos(enteredset, os.path.join(root, photo))
                    
        return enteredset
        
        
        
def myGetLocalSets(path):
    """Reads the filesystem sets"""
    if path is None:
        return None
        
    source_sets = []    
    if os.path.isdir(path):
        i=0
        misc=False
        for setname in os.listdir(path):
            fullname = os.path.join(path, setname)
            if os.path.isdir(fullname):
                source_sets.append(LocalPhotoset(i, setname, fullname))
            elif misc==False & os.path.isfile(fullname) & (fullname.lower().endswith("jpg") | fullname.endswith("JPG")):
                misc = True
                source_sets.append(LocalPhotoset(i, "misc", path))
    
    else:
        print "Path is not a known directory."
    
    return source_sets
      
        
def myGetFlickrSets():
    flickr.AUTH=True;
    me = flickr.User(myflickrinfo.FLICKRUSER)
    
    try:
        mysets = []
        mysets = me.getPhotosets()
    except IOError, error:
        print "Flickr IOError: %s" % error
        exit()
        
    return mysets 


def myGetSetPhotos(myset):
    flickr.AUTH=True;

    try:
        setphotos = []
        print "myset title =", myset.title
        setphotos = myset.getPhotos()
    except IOError, error:
        print "Flickr IOError: %s" % error
        exit()

    return setphotos


def myGetFlickrSetPhotos(myset):
    return myGetSetPhotos(myset)

    
def myFindMissingPhotoObjects(local_photosets, flickr_photosets):
            
    # Take a copy to optimize the search and not corrupt the source sets
    templocal_photosets = local_photosets[:]
    tempflickr_photosets = flickr_photosets[:]

    # If an object isnt in the local set then it needs to be added. 
    # If its in the flickr set but not in the local set this doesnt matter.
    for localsetinstance in templocal_photosets[:]:
        for flickrsetinstance in tempflickr_photosets[:]:
            if flickrsetinstance.title.rstrip('.JPG') == localsetinstance.title.rstrip('.JPG'):                
                # Remove the matching items to reduce the search space - if its in the list we dont need to check it again!
                templocal_photosets.remove(localsetinstance)
                tempflickr_photosets.remove(flickrsetinstance)
                break            

    return templocal_photosets
    
    
def myAddMissingPhotoSets(photoset_delta):
    me = flickr.User(myflickrinfo.FLICKRUSER)

    for missing_set in photoset_delta:  
        mylocal_photos = missing_set.getPhotos()
        
        print "Adding set: ", missing_set.title
        print "Missing photos:"
        
        create_set = True
        for missing_photo in mylocal_photos:
            print missing_photo.fullname
            try:
                photo = flickrupload.upload(filename=missing_photo.fullname, title=missing_photo.title.rstrip('.JPG'))
            except FlickrError:
                print "ERROR FOUND:"
            else:
                if create_set == True:
                    newphotoset = me.createPhotoset(photo, missing_set.title)
                    create_set = False
                else:
                    newphotoset.addPhoto(photo)


def myAddMissingPhotos(local_photosets, flickr_photosets):
    for local_photoset in local_photosets:
        for flickr_photoset in flickr_photosets:
            if local_photoset.title == flickr_photoset.title:
                print "Checking: ", local_photoset.title 
                # Found matching set
                local_photos = local_photoset.getPhotos()
                flickr_photos = flickr_photoset.getPhotos()
                # Now find the missing photos within this set, if any
                missing_photos = myFindMissingPhotoObjects(local_photos, flickr_photos)

                # For every missing photo add it to the identified set
                for missing_photo in missing_photos:
                    mytitle=missing_photo.title.rstrip('.JPG')
                    photo = flickrupload.upload(filename=missing_photo.fullname, title=mytitle)
                    print "Added photo: ", photo.title
                    flickr_photoset.addPhoto(photo)
                    
                    
                    
def myDownloadMissingPhotoSets(photoset_delta, path):
    print "myDownloadMissingPhotoSets"
    for missing_set in photoset_delta: 
        setPhotos = missing_set.getPhotos()    
        mySaveMissingPhoto(setPhotos, missing_set.title, path)

def mySaveMissingPhoto(missingPhotos, setTitle, path):
    fullpath = os.path.join(path, setTitle)
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)

    print fullpath
    
    for setPhoto in missingPhotos:
        sizesData = setPhoto.getSizes()
        for size in sizesData:
            if size['label'] == "Original":
                r = requests.get(size['source'], verify=False)
                print setPhoto.title
                fullname = os.path.join(fullpath.lower(), setPhoto.title + ".jpg")
                f = open(fullname, "w")
                f.write(r.content)
                f.close()                        
                    
def myDownloadMissingPhotos(local_photosets, flickr_photosets, path):
    for local_photoset in local_photosets:
        for flickr_photoset in flickr_photosets:
            if local_photoset.title == flickr_photoset.title:
                print "Checking: ", local_photoset.title 
                # Found matching set
                local_photos = local_photoset.getPhotos()
                flickr_photos = flickr_photoset.getPhotos()
                # Now find the missing photos within this set, if any
                # Needs to be switched round to get the images on flickr that arent on the local drive
                print "local: "
                myUtilOutputPhotos(local_photos)
                print "flickr: "
                myUtilOutputPhotos(flickr_photos)
                missing_photos = myFindMissingPhotoObjects(flickr_photos, local_photos) 

                # For every missing photo add it to the identified set
                mySaveMissingPhoto(missing_photos, local_photoset.title, path)

def myUtilOutputSets(myphotosets):
    for photosetinstance in myphotosets:
        print photosetinstance.title
        
    return


def myUtilOutputPhotos(myphoto):
    for instance in myphoto:
        print instance.title
        
    return

def main():
    flickr.API_KEY = myflickrinfo.API_KEY
    flickr.API_SECRET = myflickrinfo.API_SECRET

    # TODO: Fix the version substitution"
    parser = argparse.ArgumentParser(description='Flicker Upload Script.')
    parser.add_argument("-a", "--authorize", action="store_true", dest="authorize", default=False, help="Authorize the application")
    parser.add_argument("-s", "--setdiff", action="store_true", dest="setdiff", default=False, help="Display set differences")
    parser.add_argument("-i", "--imagediff", action="store_true", dest="imagediff", default=False, help="Display photo differences for specified set")
    parser.add_argument("-d", "--download", action="store_true", dest="download", default=False, help="Download from Flickr")
    parser.add_argument("-c", "--confirm", action="store_true", dest="confirm", default=True, help="Confirm creation of delta set and / or upload of image")
    parser.add_argument("-p", "--path", action="store", dest="path", help="Local image path")
    parser.add_argument('-t', '--testmode', action="store_true", default=False, dest="testMode")    
    (args) = parser.parse_args()
            
    # Rules are either:
    #    authorize 
    # Or
    #    -p <path> and -i or -s
    if (    ((args.authorize == False) & (args.path == None))  |  
            ((args.setdiff == False) & (args.imagediff == False) & (args.path != None))
        ):
        parser.error("incorrect number of arguments")

    if args.testMode == True:
        backup = sys.stdout
        sys.stdout = StringIO()

    if args.authorize:
        print "Authorize application."
        myAuthorization()

    mylocal_photosets = myGetLocalSets(args.path)    
    myflickr_photosets = myGetFlickrSets()
    
    if args.setdiff:
        # TODO: Display the set deltas between the local sets and the flickr sets 
        print "**************Display set deltas.***************************"

        if args.download:
            print "On Flickr not local"
            setdelta = myFindMissingPhotoObjects(myflickr_photosets, mylocal_photosets)
            myUtilOutputSets(setdelta)
            myDownloadMissingPhotoSets(setdelta, args.path)
        
        print "Local not on Flickr"
        setdelta = myFindMissingPhotoObjects(mylocal_photosets, myflickr_photosets)
        myUtilOutputSets(setdelta)
        
        #if args.confirm:
        print "**************Add set deltas********************************"
        myAddMissingPhotoSets(setdelta)
        print "************************************************************"
    
    if args.imagediff:
        # TODO: Display the image deltas between the specific local set and the flickr set
        print "**************Add set image deltas.********************"
        #if args.confirm:
        if args.download:
            print "On Flickr not local"
            myDownloadMissingPhotos(mylocal_photosets, myflickr_photosets, args.path)
            
        print "Local not on Flickr"
        myAddMissingPhotos(mylocal_photosets, myflickr_photosets)
        print "************************************************************"

    if args.testMode == True:
        logOutput = sys.stdout.getvalue() 
        sys.stdout.close()  
        sys.stdout = backup 

        f = open("lastexecution.log", "w")
        f.write("Executed at " + time.strftime("%a, %d %b %Y %H:%M") + "\n")
        for line in logOutput:
            f.write(line)
        f.close()        
        
if __name__ == '__main__':    
    main()
    
    
# TODO: Need to look at the implementation in the test function to see if the result that looks correct actually is.
# TODO: Need to add the "misc" exception everywhere its needed for photos in the root folder
# TODO: Start fixing Flickr error captures to prevent the crash
# TODO: Add a test mode to allow local execution and comparison. Target the local filesystem with varying flickr sets and content
# TODO: Add some code to check for authorization. If not authenticated try to perform an authentication, if that fails exit with a suitable error.
# TODO: Instead of the item above, maybe add an authorization mode and drive the execution from a command line option and use the earlier error to drive appropriately.
# TODO: Add something to fork a new process / thread to effectively get a service running


