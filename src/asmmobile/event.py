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

import datetime
import grok
import asmmobile.interfaces
from mobile import MobileView, ICalendar, VCalendar
from util import DisplayEvent

def _sortByStartTime(first, second):
    startCmp = cmp(first.start, second.start)
    if startCmp == 0:
        # In case we have same start time, compare by ID to get always correct
        # sort order.
        return cmp(first.__name__, second.__name__)
    else:
        return startCmp

class EventContainer(grok.Container):
    grok.implements(asmmobile.interfaces.IEventContainer)

    def updateEvents(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        addKeys = newKeys.difference(currentKeys)
        for key in addKeys:
            eventValues = values[key]
            self[key] = Event(name=eventValues['name'],
                              start=eventValues['start'],
                              end=eventValues['end'],
                              location=eventValues['location'],
                              url=eventValues['url'],
                              categories=eventValues['categories'],
                              )

        updateKeys = newKeys.intersection(currentKeys)
        for key in updateKeys:
            eventValues = values[key]
            event = self[key]
            event.name = eventValues['name']
            event.start = eventValues['start']
            event.end = eventValues['end']
            event.location = eventValues['location']
            event.url = eventValues['url']
            event.categories = eventValues['categories']

    def getEvents(self, eventFilter):
        events = list(self.values())
        events.sort(_sortByStartTime)
        return filter(eventFilter, events)


class Event(grok.Model):
    grok.implements(asmmobile.interfaces.IEvent)

    def __init__(self,
                 name,
                 start,
                 end,
                 location,
                 url,
                 description=None,
                 categories=[]):
        self.name = name
        self.start = start
        self.end = end
        self.location = location
        self.url = url
        self.description = description
        self.categories = categories

    def getMajorLocation(self):
        return self.location.majorLocation

    majorLocation = property(getMajorLocation)

    def getLength(self):
        return self.end - self.start

    length = property(getLength)

    def getId(self):
        return self.__name__

    id = property(getId)


class EventIndex(MobileView):
    grok.name("index")
    grok.context(Event)

    zeroSeconds = datetime.timedelta(seconds=0)

    def getTitle(self):
        return self.context.name

    title = property(getTitle)

    def update(self):
        self.mobileUpdate()


class EventIcal(ICalendar):
    grok.name("event.ics")
    grok.context(Event)

    def update(self):
        super(EventIcal, self).update()

        self.events = [DisplayEvent(self, self.context, "")]


class EventVcal(VCalendar):
    grok.name("event.vcs")
    grok.context(Event)

    def update(self):
        super(EventVcal, self).update()

        self.events = [DisplayEvent(self, self.context, "")]
