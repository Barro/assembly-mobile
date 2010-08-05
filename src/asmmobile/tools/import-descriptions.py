def parseData(filename, defaultLanguage):
    fp = open(filename, "r")
    result = {}
    currentItem = None
    for line in fp:
        line = line.strip()
        if line == "":
            continue
        elif line[0] == '!':
            currentItem = line[1:].strip()
        elif line[0] == ":":
            # Add space as description can be empty.
            line += " "
            language, description = (x.strip() for x in line[1:].split(" ", 1))
            if language not in result:
                result[language] = {}
            if description == '':
                description = result[defaultLanguage][currentItem]['description']
            result[language][currentItem] = {'description': description}
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
