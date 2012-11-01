"""Does...
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
from optparse import OptionParser

def myAuthorization(myAuth=flickr.Auth()):
    # Dont use an authorized access for this attempt
    flickr.AUTH=False;
    permission = "write"
    try:
        frob = myAuth.getFrob()
    except IOError:
        print "ERROR: Flickr Authentication error, Frob."
        exit()
    
    link = myAuth.loginLink(permission, frob)
    browser = webbrowser.get()
    browser.open(link)
    
    print "INFO: Enable authorization through the Web Browser. Hit enter once complete."
    raw_input()
    
    # Get and store the token
    try:
        token = myAuth.getToken(frob)
    except IOError:
        print "ERROR: Flickr Authentication, Token."
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
        
        # Create the full path from the possibly recursive root variabl passed in, this extends the set's root path
        fullpath = os.path.join(self.fullname, root)

        folder_content = os.listdir(fullpath)        
        i = 0;
        for photo in folder_content:
            fullname = fullpath + "\\" + photo.lower()
            
            if os.path.isfile(fullname):
                if photo.lower().endswith("jpg"):
                    # Get rid of any slashes in the root path variable and concatonate the string name
                    shortname = root.replace("\\", "") + photo.lower().strip(".jpg")                    
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
            elif misc==False & os.path.isfile(fullname) & fullname.lower().endswith("jpg"):
                misc = True
                source_sets.append(LocalPhotoset(i, "misc", path))
    
    else:
        print "INFO: Path is not a known directory."
    
    return source_sets
      
        
def myGetFlickrSets():
    flickr.AUTH=True    
    me = flickr.User(myflickrinfo.FLICKRUSER)
    
    try:
        mysets = []
        mysets = me.getPhotosets()
    except IOError, error:
        print "ERROR: Flickr IOError: %s" % error
        exit()
        
    return mysets 


def myGetSetPhotos(myset):
    flickr.AUTH=True;

    try:
        setphotos = []
        setphotos = myset.getPhotos()
    except IOError, error:
        print "ERROR: Flickr IOError: %s" % error
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
            if flickrsetinstance.title == localsetinstance.title.rstrip('.JPG'):
                # Remove the matching items to reduce the search space - if its in the list we dont need to check it again!
                templocal_photosets.remove(localsetinstance)
                tempflickr_photosets.remove(flickrsetinstance)
                break            

    return templocal_photosets
    
    
def myAddMissingPhotoSet(photoset_delta, confirmupload):
    """ Adds the set and all the photos it contains """
    testexecution = True
    
    me = flickr.User(myflickrinfo.FLICKRUSER)

    for missing_set in photoset_delta:  
        mylocal_photos = missing_set.getPhotos()
        
        create_set = True
        for missing_photo in mylocal_photos:
            
            if confirmupload == True:
                print "Do you wish to upload: ", missing_photo.title
                # TODO: Get at the command input
                skip = raw_input()
            if skip == 'Y' | skip == 'y':            
                print "Adding: ", missing_photo.title
                try:
                    if testexecution == True:
                        photo = missing_photo
                    else:
                        photo = flickrupload.upload(filename=missing_photo.fullname, title=missing_photo.title.rstrip('.JPG'))
                except FlickrError:
                    print "ERROR FOUND:"                
        
                if create_set == True:
                    print "Creating set: ", missing_set
                    if testexecution == False:
                        newphotoset = me.createPhotoset(photo, missing_set.title)
                    else:
                        print "Creating set: ", missing_set
                        newphotoset = LocalPhotoset(0, missing_set.title, missing_set.title)
                    create_set = False
                else:
                    if testexecution == False:
                        newphotoset.addPhoto(photo)


def myAddMissingPhotos(local_photosets, flickr_photosets):
    print "In addMissingPhotos"
    for local_photoset in local_photosets:
        for flickr_photoset in flickr_photosets:
            if local_photoset.title == flickr_photoset.title:
                print "Found matching set."
                # Found matching set
                local_photos = local_photoset.getPhotos()
                flickr_photos = flickr_photoset.getPhotos()
                # Now find the missing photos within this set, if any
                missing_photos = myFindMissingPhotoObjects(local_photos, flickr_photos)

                # For every missing photo add it to the identified set
                for missing_photo in missing_photos:
                    print "Missing set, photo: ", flickr_photoset.title, missing_photo.title
                    mytitle=missing_photo.title.rstrip('.JPG')
                    print "Missing set, photo: ",flickr_photoset.title, mytitle
                    photo = flickrupload.upload(filename=missing_photo.fullname, title=mytitle)
                    print "Added photo: ", photo.title
                    flickr_photoset.addPhoto(photo)


def myUtilOutputSets(myphotosets):
    for photosetinstance in myphotosets:
        print photosetinstance.title
        
    return


def myUtilOutputPhotos(myphoto):
    for instance in myphoto:
        print instance.title
        
    return

def myAuthenticated():
    try:
        flickr.User(myflickrinfo.FLICKRUSER).getPhotosets()
    except IOError:
        return False
    
    return True


def main():
    flickr.API_KEY = myflickrinfo.API_KEY
    flickr.API_SECRET = myflickrinfo.API_SECRET

    usage = "usage: %prog [options]"
    # TODO: Fix the version substitution"
    parser = OptionParser(usage, version="%prog %__version__", prog = "myflickrupload.py")
    parser.add_option("-a", "--authorize", action="store_true", dest="authorize", default=False, help="Authorize the application")
    parser.add_option("-s", "--setdiff", action="store_true", dest="setdiff", default=False, help="Display set differences")
    parser.add_option("-i", "--imagediff", action="store_true", dest="imagediff", default=False, help="Display photo differences for specified set")
    parser.add_option("-c", "--confirm", action="store_true", dest="confirm", default=True, help="Confirm creation of delta set and / or upload of image")
    parser.add_option("-p", "--path", action="store", dest="path", help="Local image path")
    parser.add_option("-u", "--upload", action="store_true", dest="upload", default=True, help="Upload the image deltas.")
    (options, args) = parser.parse_args()
    
    # Rules are either:
    #    authorize 
    # Or
    #    -p <path> and -i or -s
    
    print "options.upload: ", options.upload
    if (    ((options.authorize == False) & (options.path == None))  | 
            ((options.path != None) & (options.setdiff == False) & (options.imagediff == False) & (options.upload == False))
        ):
        parser.error("incorrect number of arguments")

    if options.authorize:
        print "ACTION: Authorize application."
        myAuthorization()
    
    if options.setdiff:
        print "ACTION: Display set deltas."
        
        if myAuthenticated() == False:
            print "INFO: Not authenticated, starting the authentication process."
            #myAuthorization()

        mylocal_photosets = myGetLocalSets(options.path)
#        myflickr_photosets = myGetFlickrSets()
        myflickr_photosets = myGetLocalSets(os.path.abspath(os.path.join(os.getcwd(), '..', 'test\\testdataflickr')))
        setdelta = myFindMissingPhotoObjects(mylocal_photosets, myflickr_photosets)
        
        for localsetdiff in setdelta:
            print "Set: ", localsetdiff.title
    
    if options.imagediff:
        # TODO: Display the image deltas between the specific local set and the flickr set
        print "ACTION: Display set image deltas."

    if options.upload:
        print "ACTION: Upload deltas."
                
        if myAuthenticated() == False:
            print "INFO: Not authenticated, starting the authentication process."
            #myAuthorization()

        mylocal_photosets = myGetLocalSets(options.path)
#        myflickr_photosets = myGetFlickrSets()
        myflickr_photosets = myGetLocalSets(os.path.abspath(os.path.join(os.getcwd(), '..', 'test\\testdataflickr')))
        setdelta = myFindMissingPhotoObjects(mylocal_photosets, myflickr_photosets)
        
        for localset in mylocal_photosets:
            if localset not in setdelta: # What are the photo deltas
#                print "Set: ", localset.title
                localphotos = localset.getPhotos()
                
                for flickrset in myflickr_photosets:
                    if flickrset.title == localset.title:
#                        print "Found matching set: ", flickrset.title
                        flickrphotos = flickrset.getPhotos()
                        
                        imagedelta = myFindMissingPhotoObjects(localphotos, flickrphotos)
#                        for image in imagedelta:
#                            print "Image Delta: ", image.title
        
        myAddMissingPhotoSet(setdelta, options.confirm)

if __name__ == '__main__':    
    main()
    
    
# TODO: Need to add the "misc" exception everywhere its needed for photos in the root folder
# TODO: Start fixing Flickr error captures to prevent the crash
# TODO: Check for memory leaks and fix.
# TODO: Add a UI. But make it command line driven so the tool can be run headless.

# TO REVIEW: What is a frob
# TO REVIEW: How the frob is used
