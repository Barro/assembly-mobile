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

import copy
import datetime
import dateutil.tz
import dateutil.parser
import re

import grok
import grok.interfaces
import grokcore.component
import grokcore.view.components
import grokcore.view.interfaces

import zope.interface
from zope.i18n import translate
from zope.interface.common.interfaces import IException
from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.app.exception.systemerror import SystemErrorView
from zope.i18n.interfaces import INegotiator, IUserPreferredLanguages
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import BrowserLanguages

import paste.httpserver

import asmmobile.interfaces as interfaces
import asmmobile.location
import asmmobile.event
import asmmobile.components
from asmmobile.components import MobileView, StylesheetManager, MobileTemplate, NavigationManager
import asmmobile.util as util
from asmmobile.util import getEventList, DisplayEvent
import asmmobile.config as config
import asmmobile.selector as selector
import asmmobile.orderby as orderby
from asmmobile import AsmMobileMessageFactory as _


# Monkey patch send_header() method not to send "Server" header.
# This saves 42 bytes when sending responses.
old_send_header = paste.httpserver.WSGIHandler.send_header
def new_send_header(self, key, value):
    if key.lower() == "server":
        return
    return old_send_header(self, key, value)
paste.httpserver.WSGIHandler.send_header = new_send_header


class CatalogBasedI18nUserPreferredLanguages(grok.Adapter):
    grok.context(IBrowserRequest)
    grok.provides(IUserPreferredLanguages)

    availableLanguages = None

    def getPreferredLanguages(self):

        if not config.enableInternalization:
            return [config.defaultLanguage]

        request = self.context

        if hasattr(request, 'locale'):
            return [request.locale.id.language]

        if self.availableLanguages is None:
            CatalogBasedI18nUserPreferredLanguages.availableLanguages = \
                util.getAvailableLanguages()

        browserLanguages = []
        if config.cookieLanguage in request.cookies:
            browserLanguages.append(request.cookies[config.cookieLanguage])

        langs = BrowserLanguages(request).getPreferredLanguages()
        for httplang in langs:
            language, country, variant = \
                (httplang.split('-') + [None, None])[:3]
            browserLanguages.append(unicode(language))

        existingLanguages = []
        for language in browserLanguages:
            if language in self.availableLanguages:
                existingLanguages.append(language)

        existingLanguages.append(config.defaultLanguage)

        uniqueLanguages = util.uniqify(existingLanguages)

        return uniqueLanguages


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


class ImportError(RuntimeError):
    def __init__(self, msg):
        self.msg = msg


DATE_FORMAT_RE = re.compile(ur"^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d\d\d$")

class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(interfaces.IAsmMobile, interfaces.IEventOwner)

    navigationName = _(u"Home")

    partyName = config.partyName

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        defaultLanguage = config.defaultLanguage

        locations = asmmobile.location.LocalizedLocationContainer()
        self[config.locations] = locations
        locations[defaultLanguage] = asmmobile.location.LocationContainer()

        events = asmmobile.event.LocalizedEventContainer()
        self[config.events] = events
        events[defaultLanguage] = asmmobile.event.EventContainer()


    @property
    def EVENTS(self):
        return self[config.events]


    @property
    def LOCATIONS(self):
        return self[config.locations]


    def getFirstEvent(self, request):
        events = self.EVENTS.get(request.locale.id.language, None)
        if events == None:
            return asmmobile.event.NoneEvent()
        return events.firstEvent


    def getLastEvent(self, request):
        events = self.EVENTS.get(request.locale.id.language, None)
        if events == None:
            return asmmobile.event.NoneEvent()
        return events.lastEvent


    def updateLocations(self, languagedLocations):
        if config.defaultLanguage not in languagedLocations:
            raise ImportError("No locations for default language.")

        locationData = {}
        for language, locations in languagedLocations.items():
            locationData[language] = {}
            for location, locationValues in locations.items():
                locationId = str(location)
                if locationId not in languagedLocations[config.defaultLanguage]:
                    raise ImportError("All locations must be available for default language.")
                locationUnicodeValues = util.unicodefyStrDict(locationValues)
                locationData[language][locationId] = locationUnicodeValues

        # Make sure that every language has all locations.
        defaultLocations = locationData[config.defaultLanguage]
        for locationId, defaultValues in defaultLocations.items():
            for languageValues in locationData.values():
                if locationId not in languageValues:
                    languageValues[locationId] = copy.copy(defaultValues)

        for languageId, locationValues in locationData.items():
            locations = self.LOCATIONS.get(languageId, None)
            if locations is None:
                locations = asmmobile.location.LocationContainer()
                self.LOCATIONS[languageId] = locations
            locations.updateLocations(locationValues)

    def _sanitizeEvent(self, locations, values):
        if 'name' not in values:
            raise ImportError("Event has to have a name")

        if 'start' not in values:
            raise ImportError("Event has to have a start time")

        if not DATE_FORMAT_RE.match(values['start']):
            print values['start']
            raise ImportError("Invalid start time format: %s" % values['start'])

        if 'end' not in values:
            values['end'] = values['start']

        if not DATE_FORMAT_RE.match(values['end']):
            raise ImportError("Invalid end time format: %s" % values['end'])

        if 'start-original' not in values:
            values['start-original'] = values['start']

        if not DATE_FORMAT_RE.match(values['start-original']):
            raise ImportError(
                "Invalid original start time time format: %s" % \
                    values['start-original'])

        eventValues = util.unicodefyStrDict(values)

        # Objectify location.
        if 'location' in values and values['location'] is not None:
            location = locations[values['location']]
        else:
            location = None
        eventValues['location'] = location


        # Objectify times.
        eventValues['start'] = dateutil.parser.parse(eventValues['start'])
        eventValues['start-original'] = dateutil.parser.parse(eventValues['start-original'])
        eventValues['end'] = dateutil.parser.parse(eventValues['end'])

        return eventValues

    def updateEvents(self, languagedEvents):
        if config.defaultLanguage not in languagedEvents:
            raise ImportError("No events for default language.")

        eventData = {}

        # Check for event sanity and objectify textual location data.
        for language, events in languagedEvents.items():
            locations = self.LOCATIONS[language]
            eventData[language] = {}
            for event, values in events.items():
                if event not in languagedEvents[config.defaultLanguage]:
                    raise ImportError("All events must be available for default language.")

                eventId = str(event)
                eventValues = self._sanitizeEvent(locations, values)
                eventData[language][eventId] = eventValues

        # Make sure that all languages have at least some version of all events.
        for eventId, values in eventData[config.defaultLanguage].items():
            for language, events in eventData.items():
                locations = self.LOCATIONS[language]
                if eventId not in events:
                    newValues = copy.copy(values)
                    location = None
                    if newValues['location'] is not None:
                        location = locations[newValues['location'].id]
                    newValues['location'] = location
                    events[eventId] = newValues

        # Update events for each language.
        for language, languageEvents in eventData.items():
            events = self.EVENTS.get(language, None)
            if events is None:
                events = asmmobile.event.EventContainer()
                self.EVENTS[language] = events
            events.updateEvents(languageEvents)

        # Remove unused languages.
        for language in self.EVENTS.keys():
            if language not in eventData:
                del(self.EVENTS[language])


    def getEvents(self, request, eventFilter=None):
        events = self.EVENTS.get(request.locale.id.language, None)
        # Fall back to default language.
        if events is None:
            events = self.EVENTS[config.defaultLanguage]
        return events.getEvents(eventFilter)


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
    grok.context(interfaces.IAsmMobile)

    def _getCurrentNextEvents(self, now):
        notEndedEvents = self.context.getEvents(self.request,
            selector.NotEndedEvents().setNow(now))

        currentEvents = filter(
            selector.CurrentEvents().setNow(now), notEndedEvents)
        currentEvents.sort(currentSort)

        self.currentEvents = getEventList(self, currentEvents)

        for nextSelector in nextSelectors:
            nextSelector.reset(now)
        nextEvents = filter(
            selector.AndSelector(nextSelectors), notEndedEvents)
        nextEvents.sort(nextSort)

        self.nextEvents = getEventList(self, nextEvents)


    def _getPartyStatus(self, now, nextEvents):
        firstEvent = self.context.getFirstEvent(self.request)
        lastEvent = self.context.getLastEvent(self.request)

        hasUpcomingEvents = len(nextEvents) > 0
        haveEvents = firstEvent != u''
        self.partyHasStarted = haveEvents and firstEvent.start <= now
        self.partyHasEnded = haveEvents and lastEvent.end < now
        partyIsOngoing = (
            haveEvents and self.partyHasStarted and not self.partyHasEnded)
        # Some event might be starting in a while so we mark party as ongoing.
        if hasUpcomingEvents or partyIsOngoing:
            self.partyIsOngoing = True
        else:
            self.partyIsOngoing = False


    def update(self):
        self._getCurrentNextEvents(self.now)
        self._getPartyStatus(self.now, self.nextEvents)


class NavigationBreadcrumbs(grok.Viewlet):
    grok.viewletmanager(NavigationManager)
    grok.context(zope.interface.Interface)

    BREADCRUMB_SEPARATOR = "<!----> &gt; <!---->"

    def render(self):
        contexts = []

        if interfaces.INavigationObject.providedBy(self.view):
            contexts.append(self.view)

        context = self.context
        while not grok.interfaces.IApplication.providedBy(context):
            if interfaces.INavigationObject.providedBy(context):
                contexts.append(context)
            context = context.__parent__

        contexts.append(context)

        contexts.reverse()

        linkContexts = contexts[:-1]

        links = []

        for context in linkContexts:
            name = translate(context.navigationName, context=self.request)
            aliasFor = getattr(context, 'aliasFor', None)
            if aliasFor is not None:
                context = context.__parent__
                aliasFor = aliasFor
            links.append("<a href='%s'>%s</a>" % (self.view.url(context, aliasFor), name))

        currentName = translate(contexts[-1].navigationName, context=self.request)
        links.append("%s" % currentName)

        return self.BREADCRUMB_SEPARATOR.join(links)


class Layout(MobileView):
    """The view that contains the main layout."""
    grok.context(zope.interface.Interface)

    sourceUrl = config.sourceUrl
    siteName = config.siteName
    mainSiteUrl = config.mainSiteUrl

    pageOverview = (_(u"Home"), '')
    pageAllEvents = (_(u"All events"), 'all#now')
    pageAbout = (_(u"About"), 'about')


class LayoutStyle(grok.Viewlet):
    grok.viewletmanager(StylesheetManager)
    grok.context(zope.interface.Interface)
    grok.order(1)


class Favicon(MobileView):
    grok.context(zope.interface.Interface)

    grok.name("favicon.ico")
    template = None

    cacheTime = util.defaultCacheTime()

    def render(self):
        return self.static.get("favicon.ico").GET()


class ScheduledEvent(grok.View):
    grok.context(DisplayEvent)


class AllEvents(MobileView):
    grok.name("all")
    grok.context(interfaces.IAsmMobile)
    grok.implements(interfaces.INavigationObject)

    navigationName = _(u"All events")

    def update(self):
        self.events = getEventList(self, self.context.getEvents(self.request))

        if len(self.events):
            self.startTime = self.events[0].start
            self.endTime = self.events[-1].end
            self.length = self.endTime - self.startTime
        else:
            self.length = datetime.timedelta(seconds=0)

        self.anchorEvent = util.findAnchorEvent(self.now, self.events)

    def lengthString(self):
        stringParts = []
        if self.length.days != 0:
            if self.length.days == 1:
                lengthDays = _(u"%d day")
            else:
                lengthDays = _(u"%d days")
            stringParts.append(translate(
                    lengthDays, context=self.request) % self.length.days)

        hours = self.length.seconds/3600
        if hours == 1:
            lengthHours = _(u"%d hour")
        else:
            lengthHours = _(u"%d hours")
        stringParts.append(translate(lengthHours, context=self.request) % hours)

        return u" ".join(stringParts)


class AllEventsStyle(grok.Viewlet):
    grok.viewletmanager(StylesheetManager)
    grok.context(interfaces.IAsmMobile)
    grok.view(AllEvents)
    grok.order(2)

class About(MobileView):
    grok.context(interfaces.IAsmMobile)

    cacheTime = util.defaultCacheTime()

    qrCodeAltTemplate = _(u"QR code link to home page (%s).")

    def update(self):
        self.qrCodeAlt = translate(
            self.qrCodeAltTemplate, context=self.request) % self.application_url()


class ErrorLayout(MobileView):
    """The view that contains the error layout."""
    grok.context(zope.interface.Interface)

    siteName = config.siteName


class Error401Unauthorized(MobileView, SystemErrorView):
     grok.context(IUnauthorized)
     grok.name('index.html')

     def update(self):
         self.siteUrl = self.url(grok.getSite())
         self.response.setStatus(401)
         self.response.setHeader("WWW-Authenticate", 'basic realm="Zope"')


class Error404NotFound(MobileView, SystemErrorView):
     grok.context(INotFound)
     grok.name('index.html')

     def update(self):
         self.siteUrl = self.url(grok.getSite())
         self.response.setStatus(404)


class Error500InternalServerError(MobileView, SystemErrorView):
     grok.context(IException)
     grok.name('index.html')

     def update(self):
         print self.context
         #import pdb; pdb.set_trace()
         self.siteUrl = self.url(grok.getSite())
         self.response.setStatus(500)


class SetLanguage(MobileView):
    grok.context(zope.interface.Interface)
    grok.name('l')

    cacheTime = util.AddTime(datetime.timedelta(seconds=0))

    def publishTraverse(self, request, name):
        self.newLanguage = name
        request.setTraversalStack([])
        return self

    def update(self):
        language = getattr(self, 'newLanguage', None)
        if language is not None:
            self.request.response.setCookie(
                config.cookieLanguage, language, path='/')

        returnTo = self.request.getHeader('Referer')
        # No referrer or referrer is the language selector view.
        if (returnTo is None or
            not returnTo.startswith(self.application_url()) or
            returnTo == self.request.getURL()):
            names = []
            context = self.context
            site = grok.getSite()
            while context != site:
                if interfaces.ILocalizedContentContainer not in \
                        zope.interface.providedBy(context.__parent__):
                    names.append(context.__name__)
                context = context.__parent__
            names.reverse()
            returnTo = "%s/%s" % (self.application_url(), "/".join(names))
        self.redirect(returnTo)

    def render(self):
        return ''
