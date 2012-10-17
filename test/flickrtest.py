import myflickrupload
import unittest
import sys

class TestFlickrFunctions(unittest.TestCase):

    def setUp(self):
        self.seq = range(10)

    #@unittest.expectedFailure
    def test_LocalSetDiff(self):
        """Check that the local set diff is correct"""
        
        myflickrupload.testexecution = True
        
        localset = myflickrupload.myGetLocalSets("C:\\Users\\mark.welsh\\Personal\\Flickr\\TestWork\\testdata")
        localflickrset = myflickrupload.myGetLocalSets("C:\\Users\\mark.welsh\\Personal\\Flickr\\TestWork\\testdataflickr")
        testsetdelta = myflickrupload.myFindMissingPhotoObjects(localset, localflickrset)

        testdelta = ["test1", "test2"]
        for deltaname in testsetdelta:
            self.assertIn(deltaname.title, testdelta)

    
    def test_LocalSetSearch(self):
        """Check that the local set search is correct"""
        testlist = ["test", "test1", "test2", "misc"]
        localset = myflickrupload.myGetLocalSets("C:\\Users\\mark.welsh\\Personal\\Flickr\\TestWork\\testdata")
        
        localsetnames = []
        for localsetitem in localset:
            localsetnames.append(localsetitem.title)
            
        testlist.sort()
        localsetnames.sort()
        self.assertTrue(testlist == localsetnames)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFlickrFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)