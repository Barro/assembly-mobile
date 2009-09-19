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
import dateutil.tz

import asmmobile.interfaces as interfaces
from asmmobile.components import MobileView
import asmmobile.util as util
import config


def _sortByStartTime(first, second):
    startCmp = cmp(first.start, second.start)
    if startCmp == 0:
        # In case we have same start time, compare by ID to always get correct
        # sort order.
        return cmp(first.__name__, second.__name__)
    else:
        return startCmp


@grok.subscribe(interfaces.IEventContainer, grok.IContainerModifiedEvent)
def notify_eventCountChanged(container, event):
    container.lastModified = util.clock()


@grok.subscribe(interfaces.IEvent, grok.IObjectModifiedEvent)
def notify_eventModified(event, modifiedEvent):
    container = event.__parent__
    container.lastModified = util.clock()


class EventContainer(grok.OrderedContainer):
    grok.implements(interfaces.IEventContainer)

    lastModified = None

    def updateEvents(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        addKeys = newKeys.difference(currentKeys)
        for key in addKeys:
            eventValues = values[key]
            self[key] = Event(
                name=eventValues['name'],
                start=eventValues['start'].astimezone(dateutil.tz.tzlocal()),
                end=eventValues['end'].astimezone(dateutil.tz.tzlocal()),
                location=eventValues['location'],
                url=eventValues.get('url', None),
                categories=eventValues.get('categories', []),
                description=eventValues.get('description', None),
                shortName=eventValues.get('short-name', eventValues['name']),
                isMajor=eventValues.get('is-major', False),
                )

        updateKeys = newKeys.intersection(currentKeys)
        for key in updateKeys:
            eventValues = values[key]
            event = self[key]
            event.name = eventValues['name']
            event.start = eventValues['start'].astimezone(dateutil.tz.tzlocal())
            event.end = eventValues['end'].astimezone(dateutil.tz.tzlocal())
            event.location = eventValues['location']
            event.url = eventValues.get('url', None)
            event.categories = eventValues.get('categories', [])
            event.description = eventValues.get('description', None)
            event.shortName = eventValues.get('short-name', eventValues['name'])
            event.isMajor = eventValues.get('is-major', False)

        # Order events by start time.
        values = list(self.values())
        values.sort(_sortByStartTime)
        self.updateOrder(order=[key.__name__ for key in values])

    def getEvents(self, eventFilter):
        return filter(eventFilter, self.values())

class EventContainerIndex(grok.View):
    grok.context(EventContainer)
    grok.name("index")

    def update(self):
        self.targetUrl = self.url(self.context.__parent__, "all-events")
        self.redirect(self.targetUrl)

    def render(self):
        pass


class Event(grok.Model):
    grok.implements(interfaces.IEvent, interfaces.IEventOwner)

    def __init__(
        self,
        name,
        start,
        end,
        location=None,
        url=None,
        description=None,
        categories=[],
        isMajor=False,
        shortName=None,
        ):
        self.name = name
        self.start = start
        self.end = end
        self.location = location
        self.url = url
        self.description = description
        self.categories = categories
        self.isMajor = isMajor
        if shortName == None:
            self.shortName = name
        else:
            self.shortName = shortName

    @property
    def majorLocation(self):
        return self.location.majorLocation

    @property
    def length(self):
        return self.end - self.start

    @property
    def id(self):
        return self.__name__

    @property
    def events(self):
        return [self]


class EventIndex(MobileView):
    grok.name("index")
    grok.context(Event)

    cacheTime = util.AddTime(datetime.timedelta(minutes=15))


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")
    grok.context(Event)
    form_fields = grok.AutoFields(Event)

    form_fields['name'].custom_widget = util.LongTextWidget
    form_fields['shortName'].custom_widget = util.LongTextWidget
    form_fields['url'].custom_widget = util.LongTextWidget
