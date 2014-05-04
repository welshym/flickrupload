import unicodedata
from cStringIO import StringIO
from xml.dom import minidom

def main():

        xmldata = open("rest.xml", "r").read()
#        updatedxmldata = unicodedata.normalize('NFKD', xmldata).encode('ascii', 'ignore')
        print minidom.parse(StringIO(xmldata))
        
  
        
if __name__ == '__main__':    
    main()
