import myflickrupload
import unittest
import sys
import os

class TestFlickrFunctions(unittest.TestCase):

    def setUp(self):
        self.seq = range(10)

    #@unittest.expectedFailure not anymore
    def test_LocalSetDiff(self):
        """Check that the local set diff is correct"""
        
        localset = myflickrupload.myGetLocalSets(os.path.abspath(os.path.join(os.getcwd(), '..', 'test\\testdata')))
        localflickrset = myflickrupload.myGetLocalSets(os.path.abspath(os.path.join(os.getcwd(), '..', 'test\\testdataflickr')))
        testsetdelta = myflickrupload.myFindMissingPhotoObjects(localset, localflickrset)

        testdelta = ["test1", "test2"]
        for deltaname in testsetdelta:
            self.assertIn(deltaname.title, testdelta)

    
    def test_LocalSetSearch(self):
        """Check that the local set search is correct"""
        testlist = ["test", "test1", "test2", "misc"]
        
        # Work out where we were called from 
        path = os.path.abspath(os.path.join(os.getcwd(), '..', 'test\\testdata'))
        if os.path.isdir(path):
            localset = myflickrupload.myGetLocalSets(path)
        else:
            localset = myflickrupload.myGetLocalSets(os.path.abspath(os.path.join(os.getcwd(), 'test\\testdata')))
        
        localsetnames = []
        for localsetitem in localset:
            localsetnames.append(localsetitem.title)
            
        testlist.sort()
        localsetnames.sort()
        # Actually needs to be assertTrue
        self.assertTrue(testlist == localsetnames)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFlickrFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)