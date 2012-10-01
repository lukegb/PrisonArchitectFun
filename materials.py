from paparse import parse_tree
import json
from pprint import pprint

def reorganise_raw_tree(tree):
    new_tree = {}
    for kk, kv in tree.iteritems():
        new_tree[kk] = dict()
        for v in kv:
            new_tree[kk][v["Name"]] = v
    return new_tree

def load_resources(f="resources/materials-new.txt"):
    cache_filename = f.replace("resources/", "resource_cache/")
    # check to see if we have a .json file there already...
    try:
        with open(cache_filename, 'r') as v:
            return json.load(v)
    except:
        pass

    # now load file
    with open(f, 'r') as v:
        tree = parse_tree(v.read())

    # organise tree into a nice dictionary
    tree = reorganise_raw_tree(tree)

    # and now save a cache
    try:
        with open(cache_filename, 'w') as v:
            json.dump(tree, v)
    except:
        pass

    return tree
    
if __name__ == '__main__':
    pprint(load_resources())
