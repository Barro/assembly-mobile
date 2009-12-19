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

import asmmobile.util as util
import asmmobile.interfaces as interfaces
import asmmobile.config as config
from asmmobile.components import MobileView, LocalizedContentContainer
from asmmobile.util import getEventList

class EditDescription(grok.Permission):
    grok.name('asmmobile.Edit')


class LocationContainer(grok.Container):
    grok.implements(interfaces.ILocationContainer)


    def touchLocation(self, keyName):
        if keyName in self:
            return self[keyName]
        else:
            location = Location(keyName, None, None)
            self[keyName] = location
            return location


    def updateLocations(self, locationValues):
        for locationKey, locationData in locationValues.items():
            location = self.touchLocation(locationKey)
            location.name = locationData.get('name', location.name)
            location.url = locationData.get('url', location.url)
            location.priority = locationData.get('priority', location.priority)
            location.hideUntil = locationData.get(
                'hideUntil', location.hideUntil)

            if 'majorLocation' in locationData:
                majorLocationKey = locationData['majorLocation']
                if majorLocationKey is not None:
                    majorLocation = self.touchLocation(majorLocationKey)
                else:
                    majorLocation = location
                location.majorLocation = majorLocation

    def application(self):
        return self.__parent__.__parent__


class Index(MobileView):
    grok.context(LocationContainer)
    grok.name("index")

    title = u"Locations"

    def locations(self):
        return self.context.values()


class Location(grok.Model):
    grok.implements(interfaces.ILocation, interfaces.IEventOwner)

    DEFAULT_PRIORITY = 0
    DEFAULT_HIDE_TIME = datetime.timedelta(seconds=config.defaultHideTime)

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

    def getHideUntil(self):
        # Get parent hiding time to be hiding time of this location.
        return self.majorLocation.hideUntil

    def getEvents(self, request):
        return self.application().getLocationEvents(request, self)

    def application(self):
        return self.__parent__.application()


class NoneLocation_cls(object):
    """This object is a placeholder location in events that do not happen
    anywhere but are just informative events."""

    grok.implements(interfaces.ILocation)

    name = u''
    url = None
    description = None

    priority = config.defaultLocationPriority
    hideUntil = datetime.timedelta(seconds=config.defaultHideTime)

    def __init__(self):
        self.majorLocation = self

    def __call__(self):
        return self


NoneLocation = NoneLocation_cls()

class LocationIndex(MobileView):
    grok.name("index")
    grok.context(Location)

    cacheTime = util.defaultCacheTime()

    zeroSeconds = datetime.timedelta(seconds=0)

    def getTitle(self):
        return self.context.name

    title = property(getTitle)

    def update(self):
        self.events = getEventList(self, self.context.getEvents(self.request))


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
