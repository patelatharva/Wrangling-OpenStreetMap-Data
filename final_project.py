import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import codecs
import json

OSMFILE = "/Users/atharva/Documents/Knowledge/practise/python/dataAnalysisDataWrangling/OpenStreetMapProject/sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", 
            "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Terrace"]

mapping = { "Dr": "Drive",                        
            "Ave": "Avenue",
            "Avenie": "Avenue",
            "Abenue": "Avenue",
            "St": "Street",
            "Blvd": "Boulevard",
            "CT": "Court",
            "Rd": "Road"            
            }
    
# Used for auditing street names in dataset

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
    
def auditStreetNames(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

    return street_types
    
# Corrects street name by replacing abbreviations and misspells with correct words
def update_name(name):
    for (bad,correction) in mapping.items():
        bad = bad.lower()
        nameInLowerCase = name.lower()        
        if nameInLowerCase.endswith(bad) or nameInLowerCase.endswith(bad+ ".") or nameInLowerCase.endswith(bad + ","):
            name = street_type_re.sub(correction,name)
    return name

# Corrects postal code by removing prefixes and suffixes
def update_postcode(postcode):
    postcode = re.sub("-\d+",'',postcode) #removes "-3131" from "94121-3131"
    postcode = re.sub("^[^\d]+", "", postcode) #remove "CA " from "CA 94605"
    return postcode
    
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

# Converts xml element into JSON object
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        if element.tag == "node":
            node["type"] = "node"
        else:
            node["type"] = "way"
        for (attribute,value) in element.attrib.items():
            if attribute not in CREATED + ["lat","lon"]:
                node[attribute] = value
            else:
                if attribute in CREATED:
                    if "created" not in node:
                        node["created"] = {}
                    node["created"][attribute] = value
                else:
                    if "pos" not in node:
                        node["pos"] = [None,None]
                    if attribute == "lat":
                        node["pos"][0] = float(value)
                    else:
                        node["pos"][1] = float(value)
                        
        for tag in element.iter("tag"):
            if "k" in tag.attrib.keys() and "v" in tag.attrib.keys():
                key = tag.attrib["k"]
                value = tag.attrib["v"]                
                if not problemchars.search(key):                        
                    if key.startswith("addr:"):                        
                        if not re.search("^addr:[\w]+:[\w]+",key):
                            if "address" not in node.keys():
                                node["address"] = {}
                            addressAttribute = re.search("^addr:(?P<addressAttribute>[\w]+)", key).group('addressAttribute')
                            if addressAttribute == "street":
                                node["address"][addressAttribute] = update_name(value)
                            elif addressAttribute == "postcode":
                                node["address"][addressAttribute] = update_postcode(value)
                            else:
                                node["address"][addressAttribute] = value
                    else:
                        if key != "address":
                            node[key] = value
        if element.tag == "way":
            node["node_refs"] = []
            for nd in element.iter("nd"):
                node["node_refs"].append(nd.attrib["ref"])        
        
        return node
    else:
        return None

def process_map(file_in, pretty = False):

    file_out = "{0}.json".format(file_in)
    
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")

if __name__ == "__main__":
    #auditStreetNames(OSMFILE)
    process_map(OSMFILE, False)