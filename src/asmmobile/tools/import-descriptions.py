def parseData(filename):
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
            language, description = (x.strip() for x in line[1:].split(" ", 1))
            if language not in result:
                result[language] = {}
            result[language][currentItem] = description
    fp.close()
    return result

def importer(locationsFile=None, eventsFile=None):
    locations = {}
    if locationsFile is not None:
        locations = parseData(locationsFile)
    events = {}
    if eventsFile is not None:
        events = parseData(eventsFile)
    return locations, events
