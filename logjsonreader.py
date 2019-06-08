import json

def readjson(jsonfile):
    trees = []
    jsonfp = open(jsonfile, "r")
    dicta = json.load(jsonfp)
    # Get all the ways until last category
    parsesons(dicta["contents"], trees)
    # Remove duplicates and format correctly
    trees = list(dict.fromkeys(trees).keys())
    trees = dict(trees)
    # The format of the tree should be now
    # , before system
    # . before category
    return trees


def parsesons(jsonlevel, trees, positiontext="_"):

    for i in jsonlevel:
        if i["type"] == "category":
            parsesons(i["contents"], trees, positiontext+i["name"] + "_")
            continue
        if i["type"] == "systems":
            for system in i["systems"]:
                trees.append(((positiontext + "·" + system["name"]).replace("_·", "·"), system["regex"]))
