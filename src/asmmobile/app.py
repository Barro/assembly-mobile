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

import grok

import grokcore.component
import grokcore.view.components
import grokcore.view.interfaces

import zope.interface
import datetime
import dateutil.tz

import re

import asmmobile.interfaces as interfaces
import asmmobile.location
import asmmobile.event
from asmmobile.components import MobileView, StylesheetManager, MobileTemplate
import asmmobile.util as util
from asmmobile.util import getEventList, DisplayEvent
import asmmobile.config as config
import asmmobile.selector as selector
import asmmobile.orderby as orderby

from asmmobile import AsmMobileMessageFactory as _

from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.app.exception.systemerror import SystemErrorView

class MobileTemplateFactory(grok.GlobalUtility):
    grok.implements(grokcore.view.interfaces.ITemplateFileFactory)
    grok.name('ptm')

    def __call__(self, filename, _prefix=None):
        return MobileTemplate(filename=filename, _prefix=_prefix)


class StylesheetTemplateFactory(grok.GlobalUtility):
    grok.implements(grokcore.view.interfaces.ITemplateFileFactory)
    grok.name('css')

    def __call__(self, filename, _prefix=None):
        return grokcore.view.components.PageTemplate(
            filename=filename, _prefix=_prefix)


class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(interfaces.IAsmMobile, interfaces.IEventOwner)

    partyName = config.partyName

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        self[config.locations] = asmmobile.location.LocationContainer()
        self[config.events] = asmmobile.event.EventContainer()


    @property
    def EVENTS(self):
        return self[config.events]


    @property
    def LOCATIONS(self):
        return self[config.locations]


    def addLocation(self, name, url, priority, hideUntil, majorLocationName):
        if isinstance(name, str):
            name = unicode(name)
        if isinstance(url, str):
            url = unicode(url)

        if majorLocationName is not None:
            majorLocation = self.LOCATIONS.getLocation(majorLocationName)
        else:
            majorLocation = None

        keyName = util.convertNameToKey(name)

        return self.LOCATIONS.addLocation(
            keyName, name, url, priority, hideUntil, majorLocation)


    def updateEvents(self, events):
        eventData = {}
        for eventId, values in events.items():
            eventValues = {}
            for key,value in values.items():
                if isinstance(value, str):
                    value = unicode(value)
                eventValues[key] = value
            location = self.LOCATIONS.getLocation(values['location'])
            eventValues['location'] = location
            eventData[eventId] = eventValues

        self.EVENTS.updateEvents(eventData)


    def getEvents(self, eventFilter=None):
        return self.EVENTS.getEvents(eventFilter)

    events = property(getEvents)


    def getLocationEvents(self, location):
        eventFilter = lambda event : (event.location == location)
        return self.EVENTS.getEvents(eventFilter)


nextSelectors = [selector.FutureEvents()]
for selectString in config.selectNextEvents.split("&"):
    selectParts = selectString.split(":", 1)
    selectName = selectParts[0]
    if len(selectParts) != 2:
        selectArgs = None
    else:
        selectArgs = selectParts[1]
    nextSelectors.append(selector.types[selectName].construct(selectArgs))

currentSort = orderby.types[config.sortCurrentEvents]
nextSort = orderby.types[config.sortNextEvents]


class Index(MobileView):
    grok.context(AsmMobile)

    def _getCurrentNextEvents(self, now):
        locations = {}

        allEvents = self.context.getEvents(
            selector.NotEndedEvents().setNow(now))

        currentEvents = filter(selector.CurrentEvents().setNow(now), allEvents)
        currentEvents.sort(currentSort)

        self.currentEvents = getEventList(
            self,
            currentEvents,
            (lambda event: event.end - now),
            (lambda event, location, outLocations:
                 outLocations[location].currentEvents.append(event)),
            locations
            )

        for nextSelector in nextSelectors:
            nextSelector.reset(now)
        nextEvents = filter(
            selector.AndSelector(nextSelectors), allEvents)
        nextEvents.sort(nextSort)

        self.nextEvents = getEventList(
            self,
            nextEvents,
            (lambda event: event.start - now),
            (lambda event, location, outLocations:
                 outLocations[location].nextEvents.append(event)),
            locations
            )

        self.LOCATIONS = locations.values()


    def _getPartyStatus(self, now, nextEvents):
        allEvents = self.context.getEvents()
        hasUpcomingEvents = len(nextEvents) > 0
        haveEvents = len(allEvents) > 0
        self.partyHasStarted = haveEvents and allEvents[0].start <= now
        self.partyHasEnded = haveEvents and allEvents[-1].end < now
        partyIsOngoing = (
            haveEvents and self.partyHasStarted and not self.partyHasEnded)
        # Event might be starting in a while so we event can be ongoing even
        # though no event has started yet.
        if hasUpcomingEvents or partyIsOngoing:
            self.partyIsOngoing = True
        else:
            self.partyIsOngoing = False


    def update(self):
        self._getCurrentNextEvents(self.now)
        self._getPartyStatus(self.now, self.nextEvents)


class NextEvents(MobileView):
    grok.name("next-events")
    grok.context(AsmMobile)

    startDifference = datetime.timedelta(hours=config.nextEventsEndHours)
    endDifference = datetime.timedelta(hours=config.nextEventsStartHours)

    differenceHours = config.nextEventsStartHours + config.nextEventsEndHours

    dateFormat = "%Y-%m-%d-%H"
    dateValidate = re.compile(r"\d\d\d\d-\d\d-\d\d-\d\d")

    def update(self, s=None):
        displayCenter = self.now
        try:
            if s is not None and self.dateValidate.match(s):
                year, month, day, hour = (int(x) for x in s.split("-"))
                displayCenter = datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    tzinfo=dateutil.tz.tzlocal()
                    )
        # ValueError happens when time matches validation regular expression
        # but is evaluated as invalid date.
        except ValueError, e:
            pass

        # Round to next full hour.
        secondsTillNextHour = \
            (3600 - (displayCenter.second + displayCenter.minute * 60))%3600
        displayCenter += datetime.timedelta(seconds=secondsTillNextHour)

        displayStart = displayCenter - self.startDifference
        displayEnd = displayCenter + self.endDifference

        self.previousCenter = \
            (displayStart - self.endDifference).strftime(self.dateFormat)
        self.nextCenter = \
            (displayEnd + self.startDifference).strftime(self.dateFormat)

        events = self.context.getEvents(
            (lambda event: displayStart < event.end
             and event.start <= displayEnd))

        # If the first displayable event is the same as the first event out of
        # all events, we don't have any more events in past and disable the
        # "previous 24 hours" link.
        allEvents = self.context.getEvents()
        if len(events) > 0 and events[0] != allEvents[0]:
            self.showPrevious = True
        else:
            self.showPrevious = False

        # If the first displayable event is the same as the last event out of
        # all events, we don't have any more events in future and disable the
        # "next 24 hours" link.
        if len(events) > 0 and events[-1] != allEvents[-1]:
            self.showNext = True
        else:
            self.showNext = False

        self.events = getEventList(self,
                                   events,
                                   (lambda event: event.length),
                                   (lambda event, location, outLocations: True),
                                   {})
        self.anchorEvent = None
        previousEvent = None
        for event in self.events:
            if event.start >= self.now:
                self.anchorEvent = previousEvent
                break
            previousEvent = event


class NextEventsStyle(grok.Viewlet):
    grok.viewletmanager(StylesheetManager)
    grok.context(AsmMobile)
    grok.view(NextEvents)


class Layout(MobileView):
    """The view that contains the main layout."""
    grok.context(zope.interface.Interface)

    sourceUrl = config.sourceUrl
    siteName = config.siteName
    mainSiteUrl = config.mainSiteUrl


class LayoutStyle(grok.Viewlet):
    grok.viewletmanager(StylesheetManager)
    grok.context(zope.interface.Interface)


class Favicon(MobileView):
    grok.context(zope.interface.Interface)

    grok.name("favicon.ico")
    template = None

    cacheTime = asmmobile.util.AddTime(datetime.timedelta(minutes=15))

    def render(self):
        return self.static.get("favicon.ico").GET()


class ScheduledEvent(grok.View):
    grok.context(DisplayEvent)


class AllEvents(MobileView):
    grok.name("all-events")
    grok.context(AsmMobile)

    cacheTime = asmmobile.util.AddTime(datetime.timedelta(minutes=15))

    def update(self):

        self.events = getEventList(self,
                                   self.context.getEvents(),
                                   (lambda event: event.length),
                                   (lambda event, location, outLocations: True),
                                   {})

        if len(self.events):
            self.length = self.events[-1].end - self.events[0].start
        else:
            self.length = datetime.timedelta(seconds=0)


class Error404NotFound(MobileView, SystemErrorView):
     grok.context(INotFound)
     grok.name('index.html')

     def update(self):
         self.siteName = config.siteName
         self.sourceUrl = config.sourceUrl
         self.siteUrl = self.url(grok.getSite())
         self.response.setStatus(404)
