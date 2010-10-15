#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2009  Assembly Organizing
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import asmmobile.util
import re
import transaction
import zope.app.component.hooks
import zope.component

def touchDict(obj, name):
    if name not in obj:
        obj[name] = {}
    return obj[name]

def mergeDataValues(fromDict, toDict):
    result = toDict
    for language, languageItems in fromDict.items():
        languageResult = touchDict(result, language)
        for itemId, data in languageItems.items():
            languageItem = touchDict(languageResult, itemId)
            for name, value in data.items():
                languageItem[name] = value
    return result


def addSpacesAroundSpacedTags(text):
    """Adds special space character around tags.

    Before output, all extra white space is filtered out and if there is
    white space around tags, it will also be filtered out from the output.
    This adds <!----> to text so that spaces are maintained after filtering
    where <!----> is added.
    """

    result = text
    result = re.sub(">\s+", "><!----> ", result)
    result = re.sub("\s+<", " <!----><", result)

    return result


def escapeDescription(event):
    if event.get('description', None) is not None:
        event['description'] = addSpacesAroundSpacedTags(event['description'])


def addShortName(event):
    import asmmobile.config

    shortName = event.get('short-name', event['name'])
    shortName = asmmobile.util.shortenName(
        name=shortName,
        maximumLength=asmmobile.config.shortNameMaximumLength,
        shortenTo=asmmobile.config.shortNameShortenTo,
        nonWordCharacters=asmmobile.config.shortNameNonWordCharacters,
        cutPostfix=asmmobile.config.shortNameCutPostfix,
        )
    event['short-name'] = shortName


def updateSchedule(app, config):
    importFuncs = {}
    for importer,arguments in config.IMPORTERS.items():
        importerModule = "import-%s" % importer
        importFunc = \
            __import__(importerModule, globals(), locals(), [], -1).importer
        importFuncs[importFunc] = arguments

    locations = {}
    events = {}

    for importer, params in importFuncs.items():
        importedLocations, importedEvents = importer(**params)
        locations = mergeDataValues(importedLocations, locations)
        events = mergeDataValues(importedEvents, events)

    # Add location mappings:
    for language, locationData in locations.items():
        for fromLocation, toLocation in config.MAPPING_LOCATIONS.items():
            # Only map location if fromLocation exists.
            if fromLocation in locationData:
                locationData[fromLocation]['majorLocation'] = toLocation
                if toLocation not in locations:
                    locationData[toLocation] = {'name': toLocation}

    # Set priorities:
    for language, locationData in locations.items():
        for id, data in locationData.items():
            data['priority'] = config.PRIORITIES.get(id, None)

    # Post-process events.
    for languageEvents in events.values():
        for event in languageEvents.values():
            addShortName(event)
            escapeDescription(event)

    zope.app.component.hooks.setSite(app)
    app.updateLocations(locations)
    app.updateEvents(events)
    transaction.commit()
