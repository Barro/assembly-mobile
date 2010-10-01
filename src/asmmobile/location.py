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
import string
import re

import grok

from asmmobile import AsmMobileMessageFactory as _
import asmmobile.util as util
import asmmobile.interfaces as interfaces
from asmmobile.components import MobileView
from asmmobile.interfaces import ILocalizedContentContainer
from asmmobile.util import getEventList

def _sortByName(first, second):
    nameCmp = cmp(first.name, second.name)
    if nameCmp == 0:
        # In case we have same name (shouldn't happen), compare by ID to
        # always get correct sort order.
        return cmp(first.id, second.id)
    else:
        return nameCmp


@grok.subscribe(interfaces.IEvent, grok.IObjectModifiedEvent)
def notify_eventModified(event, modifiedEvent):
    now = util.clock()
    event.location.lastModified = now


class EditDescription(grok.Permission):
    grok.name('asmmobile.Edit')


class LocalizedLocationContainer(grok.Container):
    grok.implements(ILocalizedContentContainer)

    navigationName = _(u"Locations")

    def application(self):
        return self.__parent__.application()


class LocationContainer(grok.OrderedContainer):
    grok.implements(interfaces.ILocationContainer)


    def _touchLocation(self, keyName):
        if keyName in self:
            return self[keyName]
        else:
            location = Location(keyName, None, None)
            self[keyName] = location
            return location

    def updateLocations(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        for locationKey, locationData in values.items():
            location = self._touchLocation(locationKey)

            if 'major-location' in locationData:
                majorLocationKey = locationData['major-location']
                if majorLocationKey is not None:
                    majorLocation = self._touchLocation(majorLocationKey)
                else:
                    majorLocation = location
                locationData['major-location'] = majorLocation

            util.setObjectAttributesFromDict(
                location,
                locationData,
                ['name',
                 'url',
                 'description',
                 'priority',
                 ('hideUntil', 'hide-until'),
                 ('majorLocation', 'major-location'),
                 ])

        # Order locations by their name.
        values = list(self.values())
        values.sort(_sortByName)
        self.updateOrder(order=[key.id for key in values])


    def application(self):
        return self.__parent__.__parent__


class Index(MobileView):
    grok.context(LocalizedLocationContainer)
    grok.name("index")

    def update(self):
        content = self.context.get(self.request.locale.id.language, None)
        if content is None:
            content = self.context[config.defaultLanguage]
        self.locations = content.values()


class Location(grok.Model):
    grok.implements(interfaces.ILocation, interfaces.IEventOwner)

    DEFAULT_PRIORITY = 0

    def _initialize(config):
        cls = Location
        cls.DEFAULT_HIDE_TIME = datetime.timedelta(seconds=config.defaultHideTime)

    util.runDeferred(_initialize)

    def __init__(self,
                 id,
                 name,
                 url,
                 description=None,
                 priority=None,
                 hideUntil=None,
                 majorLocation=None):
        self.id = id
        self.name = name
        self.url = url
        self.description = description

        if priority is None:
            self.priority = Location.DEFAULT_PRIORITY
        else:
            self.priority = priority

        if hideUntil is None:
            self.hideUntil = Location.DEFAULT_HIDE_TIME
        else:
            self.hideUntil = hideUntil

        if majorLocation is None:
            self.majorLocation = self
        else:
            self.majorLocation = majorLocation

        self.lastModified = util.clock()

    def getHideUntil(self):
        # Get parent hiding time to be hiding time of this location.
        return self.majorLocation.hideUntil

    def application(self):
        return self.__parent__.application()

    @property
    def navigationName(self):
        return self.name

    # interfaces.IEventOwner methods

    def getEvents(self, request):
        eventFilter = lambda event : (event.location == self)
        return self.application().getEvents(request, eventFilter)

    def getLastModified(self, request):
        return self.lastModified


class NoneLocation_cls(object):
    """This object is a placeholder location in events that do not happen
    anywhere but are just informative events."""

    grok.implements(interfaces.ILocation)

    name = u''
    url = None
    description = None

    def _initialize(config):
        cls = NoneLocation_cls
        cls.priority = config.defaultLocationPriority
        cls.hideUntil = datetime.timedelta(seconds=config.defaultHideTime)

    util.runDeferred(_initialize)

    def __init__(self):
        self.majorLocation = self

    def __call__(self):
        return self


NoneLocation = NoneLocation_cls()

class LocationIndex(MobileView):
    grok.name("index")
    grok.context(Location)

    def _initialize(config):
        cls = LocationIndex
        cls.cacheTime = util.defaultCacheTime(config)

    util.runDeferred(_initialize)

    zeroSeconds = datetime.timedelta(seconds=0)

    def getTitle(self):
        return self.context.name

    title = property(getTitle)

    def update(self):
        self.events = getEventList(self, self.context.getEvents(self.request))

        lastModified = self.context.getLastModified(self.request)
        self.request.response.setHeader(
            'Last-Modified', util.httpTime(lastModified))


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")
    grok.context(Location)

    form_fields = grok.AutoFields(Location)
    form_fields['name'].custom_widget = util.LongTextWidget
    form_fields['url'].custom_widget = util.LongTextWidget


class ViewUrl(grok.View):
    grok.name("url")
    grok.context(Location)

    def render(self):
        return "%s/%s" % (util.applicationRelativeUrl(self, 'location'),
                          self.context.id)

class NoneUrl(grok.View):
    grok.name("url")
    grok.context(NoneLocation_cls)

    def render(self):
        return None


class ViewLink(grok.View):
    grok.name("link")
    grok.context(Location)

    def relativeUrl(self):
        return "%s/%s" % (util.applicationRelativeUrl(self, 'location'),
                          self.context.id)


class NoneLink(grok.View):
    grok.name("link")
    grok.context(NoneLocation_cls)

    def render(self):
        return ""
