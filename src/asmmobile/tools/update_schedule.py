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


import zope.app.component.hooks
import zope.component
import transaction
import asmmobile.config
import asmmobile.util

def touchDict(obj, name):
    if name not in obj:
        obj[name] = {}
    return obj

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
        for language, languageLocations in importedLocations.items():
            locations = touchDict(locations, language)
            for locationId, data in languageLocations.items():
                locations[language][locationId] = data

        for language, languageEvents in importedEvents.items():
            events = touchDict(events, language)
            for eventId, eventParams in languageEvents.items():
                if eventId in events[language]:
                    raise Exception("Duplicate event ID: %s (%s)" % \
                                        (eventId, eventParams))
                events[language][eventId] = eventParams

    mappingLocations = {}
    for language, fromToLocations in config.MAPPING_LOCATIONS.items():
        for fromLocation, toLocation in fromToLocations.items():
            app.addLocation(toLocation.lower(), language, toLocation, None, None, None, None)
            app.addLocation(toLocation.lower(), language, fromLocation, None, None, None, toLocation)
            locations[language][toLocation.lower()] = {'name': toLocation}

    zope.app.component.hooks.setSite(app)
    for language, locationData in locations.items():
        for id, data in locationData.items():
            if id is None:
                continue
            name = data.get('name', id)
            url = data.get('url', None)
            priority = config.PRIORITIES.get(id, None)
            app.addLocation(id, language, name, url, priority, None, None)

    for eventData in events.values():
        for event in eventData.values():
            shortName = event.get('short-name', event['name'])
            shortName = asmmobile.util.shortenName(
                name=shortName,
                maximumLength=asmmobile.config.shortNameMaximumLength,
                shortenTo=asmmobile.config.shortNameShortenTo,
                nonWordCharacters=asmmobile.config.shortNameNonWordCharacters,
                cutPostfix=asmmobile.config.shortNameCutPostfix,
                )
            event['short-name'] = shortName

    app.updateEvents(events)
    transaction.commit()
