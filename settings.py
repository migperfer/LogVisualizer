import logjsonreader
"""
This is just a file to hold the common variables between diferent files, like menu.py and logVisualizer.py
All of them just import with a * this module so they can share the variables between them, those variables are:

win : Holds the main window of the program.

regexs : Is a dictionary which holds all the regexs in the logparser.json file. The keys are the name of the
filter, including all the way to it. _category_subcategory_subsubcategory·finalregex. The values inside the
keys are the regular expressions.

regexscolours : Holds a dictionary in which keys are the same that on regexs, but contains the hex format of the colors
assigned to each category.

regexsfilter : Holds a dictionary in which keys are the same that on regexs, but contains a boolean indicating if the
filter should be displayed.

regexindex : Holds a dictionary in which keys are the same that on regexs, a number indicating the last match of that
regex that was shown on screen with the search method.
"""
win = []
regexs = logjsonreader.readjson("logparser.json")
regexscolours = {}
regexsfilter = regexs.copy()
regexindex = regexs.copy()