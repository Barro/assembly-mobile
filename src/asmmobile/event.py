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
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.component import getMultiAdapter
import zope.traversing.browser.interfaces

from asmmobile import AsmMobileMessageFactory as _
import asmmobile.interfaces as interfaces
from asmmobile.components import MobileView
import asmmobile.util as util
import asmmobile.location


def _sortByStartTime(first, second):
    startCmp = cmp(first.start, second.start)
    if startCmp != 0:
        return startCmp
    if first.order != second.order:
        return cmp(first.order, second.order)
    return cmp(first.id, second.id)



def getNoneUtcTime(timeObject):
    if timeObject is None:
        return None
    return timeObject.utctimetuple()


@grok.subscribe(interfaces.IEvent, grok.IObjectModifiedEvent)
def notify_eventModified(event, modifiedEvent):
    now = util.clock()
    event.lastModified = now

    event.utcStart = getNoneUtcTime(event.start)
    event.utcStartOriginal = getNoneUtcTime(event.startOriginal)
    event.utcEnd = getNoneUtcTime(event.end)
    event.utcLastModified = getNoneUtcTime(event.lastModified)

    container = event.__parent__
    container.lastModified = now


class NoneEvent(grok.Model):
    grok.implements(interfaces.IEvent)

    id = u''
    name = u''
    shortName = u''
    # start > end so that this screws something up.
    start = datetime.datetime(datetime.MAXYEAR,12,30,tzinfo=dateutil.tz.tzlocal())
    utcStart = start.utctimetuple()
    startOriginal = start
    utcStartOriginal = startOriginal.utctimetuple()
    end = datetime.datetime(datetime.MINYEAR,1,1,tzinfo=dateutil.tz.tzlocal())
    utcEnd = end.utctimetuple()
    location = None
    url = None
    description = None
    categories = []
    isMajor = False
    canceled = False
    order = 0


class LocalizedEventContainer(grok.Container):
    grok.implements(interfaces.ILocalizedContentContainer)

    navigationName = _(u"All events")

    aliasFor = "all"

    def application(self):
        return self.__parent__.application()


class EventContainer(grok.OrderedContainer):
    grok.implements(interfaces.IEventContainer)

    lastModified = datetime.datetime(1970, 1, 1, tzinfo=dateutil.tz.tzlocal())

    firstEvent = NoneEvent()
    lastEvent = firstEvent

    def _touchEvent(self, keyName):
        if keyName in self:
            return self[keyName]
        else:
            event = Event(keyName, None, None, None)
            self[keyName] = event
            grok.notify(grok.ObjectCreatedEvent(event))
            return event


    def updateEvents(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        localTz = dateutil.tz.tzlocal()
        for key, eventData in values.items():
            eventData['start'] = eventData['start'].astimezone(localTz)
            eventData['end'] = eventData['end'].astimezone(localTz)
            if 'start-original' in eventData:
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
                 'canceled',
                 'order',
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

    _start = None
    startOriginal = None
    order = 0

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
        lastModified=None,
        startOriginal=None,
        canceled=False,
        order=0,
        ):
        self.id = id
        self.name = name
        self.start = start
        self.utcStart = getNoneUtcTime(self.start)
        if startOriginal is None:
            self.startOriginal = start
        else:
            self.startOriginal = startOriginal
        self.utcStartOriginal = getNoneUtcTime(self.startOriginal)
        self.end = end
        self.utcEnd = getNoneUtcTime(self.end)
        self._location = location
        self.url = url
        self.description = description
        self.categories = categories
        self.isMajor = isMajor
        if shortName is None:
            self.shortName = name
        else:
            self.shortName = shortName
        self.lastModified = lastModified
        self.utcLastModified = getNoneUtcTime(self.lastModified)
        self.canceled = canceled
        self.order = order

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

    @property
    def navigationName(self):
        return self.shortName

    # interfaces.IEventOwner methods

    def getEvents(self, request):
        return [self]

    def getLastModified(self, request):
        return self.lastModified

    def setStart(self, start):
        self._start = start
        if self.startOriginal is None:
            self.startOriginal = start

    def getStart(self):
        return self._start

    start = property(getStart, setStart)


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

    def update(self):
        self.displayData = util.DisplayEvent(self, self.context)
        self.request.response.setHeader(
            'Last-Modified', util.httpTime(self.context.lastModified))


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")
    grok.context(Event)
    form_fields = grok.AutoFields(Event)

    form_fields['name'].custom_widget = util.LongTextWidget
    form_fields['shortName'].custom_widget = util.LongTextWidget
    form_fields['url'].custom_widget = util.LongTextWidget


class EventStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.components.StylesheetManager)
    grok.context(interfaces.IEvent)
    grok.view(EventIndex)
    grok.order(2)


class EventAbsoluteUrl(grok.MultiAdapter):
    grok.adapts(interfaces.IEvent, IBrowserRequest)
    grok.implements(zope.traversing.browser.interfaces.IAbsoluteURL)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        application = grok.getApplication()
        application_url = getMultiAdapter(
            (application, self.request),
            zope.traversing.browser.interfaces.IAbsoluteURL)()

        stacked_objects = []
        context = self.context
        while context != application:
            if not interfaces.IEventContainer.providedBy(context):
                stacked_objects.append(context.__name__)
            context = context.__parent__
        stacked_objects.append(application_url)
        return "/".join(reversed(stacked_objects))
