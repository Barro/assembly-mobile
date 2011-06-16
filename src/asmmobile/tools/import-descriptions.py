def parseData(filename, defaultLanguage):
    fp = open(filename, "r")
    result = {}
    currentItem = None
    currentName = None
    for line in fp:
        line = line.strip()
        if line == "":
            continue
        elif line[0] == '!':
            currentItem = line[1:].strip()
            if "|" in currentItem:
                currentItem, currentName = currentItem.split("|", 1)
            else:
                currentName = None
        elif line[0] == ":":
            # Add space as description can be empty.
            line += " "
            language, description = (x.strip() for x in line[1:].split(" ", 1))
            if language not in result:
                result[language] = {}
            if description == '' and currentItem in result[defaultLanguage]:
                description = result[defaultLanguage][currentItem]['description']
            if description != '':
                result[language][currentItem] = {'description': description}
                if currentName is not None:
                    result[language][currentItem]['name'] = currentName
    fp.close()
    return result

def importer(locationsFile=None, eventsFile=None, defaultLanguage='en'):
    locations = {}
    if locationsFile is not None:
        locations = parseData(locationsFile, defaultLanguage)
    events = {}
    if eventsFile is not None:
        events = parseData(eventsFile, defaultLanguage)
    return locations, events
