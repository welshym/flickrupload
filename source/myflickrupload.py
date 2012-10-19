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
            if flickrsetinstance.title == localsetinstance.title.rstrip('.JPG'):
                # Remove the matching items to reduce the search space - if its in the list we dont need to check it again!
                templocal_photosets.remove(localsetinstance)
                tempflickr_photosets.remove(flickrsetinstance)
                break            

    return templocal_photosets
    
    
def myAddMissingPhotoSet(photoset_delta):
    me = flickr.User(myflickrinfo.FLICKRUSER)

    for missing_set in photoset_delta:      
        print missing_set.title
    
    for missing_set in photoset_delta:  
        print "Missing set is ", missing_set.title
        mylocal_photos = missing_set.getPhotos()
        
        print "Adding set: ", missing_set.title
        print "Missing photos:"
        print ""
        
        create_set = True
        for missing_photo in mylocal_photos:
            print missing_photo.title
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
    (options, args) = parser.parse_args()
    
#    mylocal_photosets = myGetLocalSets(options.path)
#    for localset in mylocal_photosets:
#        photos = myGetSetPhotos(localset)
#        print "Set: ", localset.title
#        print "Fullname: ", localset.fullname
#        for image in photos:
#            print image.title
#        print "\n\n"
#
#    return
    flickrsets = myGetFlickrSets()
    print "Output flickr sets:"
    myUtilOutputSets(flickrsets)
    
    for flickrset in flickrsets:
        flickrphotos = myGetFlickrSetPhotos(flickrset)
        print ""
        for photo in flickrphotos:
            print photo.title
    
    return
    
    
    # Rules are either:
    #    authorize 
    # Or
    #    -p <path> and -i or -s
    if (    ((options.authorize == False) & (options.path == None))  |  
            ((options.setdiff == False) & (options.imagediff == False) & (options.path != None))
        ):
        parser.error("incorrect number of arguments")

    if options.authorize:
        print "Authorize application."
        myAuthorization()
    
    if options.setdiff:
        # TODO: Display the set deltas between the local sets and the flickr sets 
        print "Display set deltas."
        mylocal_photosets = myGetLocalSets(options.path)
        myflickr_photosets = myGetFlickrSets()
        setdelta = myFindMissingPhotoObjects(mylocal_photosets, myflickr_photosets)
        myUtilOutputSets(setdelta)
        
        for localset in mylocal_photosets:
            print ""
            print ""
            print "Set: ", localset.title
            photos = myGetSetPhotos(localset)
#            print "\n\n"
#            print "Set: ", localset.title
#            print "Fullname: ", localset.fullname
#            for image in photos:
#                print image.title
    
    if options.imagediff:
        # TODO: Display the image deltas between the specific local set and the flickr set
        print "Display set image deltas."



if __name__ == '__main__':    
    main()
    
    
# TODO: Need to look at the implementation in the test function to see if the result that looks correct actually is.
# TODO: Need to add the "misc" exception everywhere its needed for photos in the root folder
# TODO: Start fixing Flickr error captures to prevent the crash
# TODO: Add a test mode to allow local execution and comparison. Target the local filesystem with varying flickr sets and content
# TODO: Add some code to check for authorization. If not authenticated try to perform an authentication, if that fails exit with a suitable error.
# TODO: Instead of the item above, maybe add an authorization mode and drive the execution from a command line option and use the earlier error to drive appropriately.
# TODO: Add something to fork a new process / thread to effectively get a service running


