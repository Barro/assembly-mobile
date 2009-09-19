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
        for name, url in importedLocations.items():
            locations[name] = url

        for eventId, eventParams in importedEvents.items():
            if eventId in events:
                raise Exception("Duplicate event ID: %s (%s)" % \
                                    (eventId, eventParams))
            events[eventId] = eventParams

    mappingLocations = {}
    for fromLocation, toLocation in config.MAPPING_LOCATIONS.items():
        app.addLocation(toLocation, None, None, None, None)
        app.addLocation(fromLocation, None, None, None, toLocation)
        locations[toLocation] = None

    zope.app.component.hooks.setSite(app)
    for name,url in locations.items():
        priority = config.PRIORITIES.get(name, None)
        app.addLocation(name, url, priority, None, None)

    for event in events.values():
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
