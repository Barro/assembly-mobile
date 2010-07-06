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

from zope.i18n import translate

from asmmobile import AsmMobileMessageFactory as _
import asmmobile.interfaces as interfaces
from asmmobile.components import MobileView
import asmmobile.util as util
import asmmobile.location

def _sortByStartTime(first, second):
    startCmp = cmp(first.start, second.start)
    if startCmp == 0:
        # In case we have same start time, compare by ID to always get correct
        # sort order.
        return cmp(first.id, second.id)
    else:
        return startCmp


@grok.subscribe(interfaces.IEventContainer, grok.IContainerModifiedEvent)
def notify_eventCountChanged(container, event):
    container.lastModified = util.clock()


@grok.subscribe(interfaces.IEvent, grok.IObjectModifiedEvent)
def notify_eventModified(event, modifiedEvent):
    container = event.__parent__
    container.lastModified = util.clock()


class NoneEvent(grok.Model):
    grok.implements(interfaces.IEvent)

    id = u''
    name = u''
    shortName = u''
    # start > end so that this screws something up.
    start = datetime.datetime(datetime.MAXYEAR,12,30,tzinfo=dateutil.tz.tzlocal())
    startOriginal = start
    end = datetime.datetime(datetime.MINYEAR,1,1,tzinfo=dateutil.tz.tzlocal())
    location = None
    url = None
    description = None
    categories = []
    isMajor = False


class LocalizedEventContainer(grok.Container):
    grok.implements(interfaces.ILocalizedContentContainer)

    navigationName = _(u"All events")

    aliasFor = "all"

    def application(self):
        return self.__parent__.application()


class EventContainer(grok.OrderedContainer):
    grok.implements(interfaces.IEventContainer)

    lastModified = None

    firstEvent = NoneEvent()
    lastEvent = firstEvent

    def _touchEvent(self, keyName):
        if keyName in self:
            return self[keyName]
        else:
            event = Event(keyName, None, None, None)
            self[keyName] = event
            return event


    def updateEvents(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        addKeys = newKeys.difference(currentKeys)
        localTz = dateutil.tz.tzlocal()
        for key, eventData in values.items():
            eventData['start'] = eventData['start'].astimezone(localTz)
            eventData['end'] = eventData['end'].astimezone(localTz)
            eventData['start-original'] = eventData['start-original'].astimezone(localTz)
            if 'short-name' not in eventData:
                eventData['short-name'] = eventData['name']

            event = self._touchEvent(key)
            util.setObjectAttributesFromDict(
                event,
                eventData,
                ['name',
                 'start',
                 ('startOriginal', 'start-original'),
                 'end',
                 'location',
                 'url',
                 'categories',
                 'description',
                 ('shortName', 'short-name'),
                 ('isMajor', 'is-major'),
                 ])

        # Order events by start time.
        values = list(self.values())
        values.sort(_sortByStartTime)
        self.updateOrder(order=[key.id for key in values])

        if len(values) != 0:
            self.firstEvent = values[0]
            self.lastEvent = values[-1]
        else:
            self.firstEvent = NoneEvent()
            self.lastEvent = self.firstEvent


    def getEvents(self, eventFilter):
        return filter(eventFilter, self.values())


class EventContainerIndex(grok.View):
    grok.context(LocalizedEventContainer)
    grok.name("index")

    def update(self):
        self.targetUrl = self.application_url("all")
        self.redirect(self.targetUrl)

    def render(self):
        pass


class Event(grok.Model):
    grok.implements(interfaces.IEvent, interfaces.IEventOwner)

    def __init__(
        self,
        id,
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
        self.id = id
        self.name = name
        self.start = start
        self.startOriginal = start
        self.end = end
        self._location = location
        self.url = url
        self.description = description
        self.categories = categories
        self.isMajor = isMajor
        if shortName == None:
            self.shortName = name
        else:
            self.shortName = shortName

    def getLocation(self):
        if self._location is None:
            return asmmobile.location.NoneLocation
        return self._location

    def setLocation(self, location):
        self._location = location

    location = property(getLocation, setLocation)

    @property
    def majorLocation(self):
        return self.location.majorLocation

    @property
    def length(self):
        return self.end - self.start

    def getEvents(self, request):
        return [self]

    @property
    def navigationName(self):
        return self.shortName


class EventIndex(MobileView):
    grok.name("index")
    grok.context(Event)

    def _initialize(config):
        cls = EventIndex
        cls.cacheTime = util.defaultCacheTime(config)

    util.runDeferred(_initialize)

    @property
    def displayName(self):
        if self.context.isMajor:
            return translate(
                _(u"%s (major event)"), context=self.request) % self.context.name
        else:
            return self.context.name


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")
    grok.context(Event)
    form_fields = grok.AutoFields(Event)

    form_fields['name'].custom_widget = util.LongTextWidget
    form_fields['shortName'].custom_widget = util.LongTextWidget
    form_fields['url'].custom_widget = util.LongTextWidget
