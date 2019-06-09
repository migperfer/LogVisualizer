import logjsonreader

win = []
regexs = logjsonreader.readjson("logparser.json")
regexscolours = {}
regexsfilter = regexs.copy()
regexindex = regexs.copy()