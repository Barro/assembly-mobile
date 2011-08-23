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
import cgi
import re

import grok
import grok.interfaces
import grokcore.component
import grokcore.view.components
import grokcore.view.interfaces

import persistent
import zope.app.wsgi.interfaces
import zope.component
from zope.i18n import translate
import zope.interface
from zope.interface.common.interfaces import IException
import zope.publisher.interfaces.http
from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import BrowserLanguages

import paste.httpserver

import asmmobile.interfaces as interfaces
import asmmobile.location
import asmmobile.event
import asmmobile.components
from asmmobile.components import MobileView
import asmmobile.util as util
from asmmobile.util import getEventList, DisplayEvent
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
# Make sure that headers and content are not sent in separate packets.
paste.httpserver.WSGIHandler.wbufsize = -1


class CatalogBasedI18nUserPreferredLanguages(grok.Adapter):
    grok.context(IBrowserRequest)
    grok.provides(IUserPreferredLanguages)

    def getPreferredLanguages(self):
        try:
            application = grok.getApplication()
        except ValueError:
            return []

        if not application.enableInternalization:
            return [application.defaultLanguage]

        request = self.context

        if hasattr(request, 'locale'):
            if request.locale.id.language is not None:
                return [request.locale.id.language]

        browserLanguages = []
        if application.languageCookie in request.cookies:
            browserLanguages.append(request.cookies[application.languageCookie])

        langs = BrowserLanguages(request).getPreferredLanguages()
        for httplang in langs:
            language, country, variant = \
                (httplang.split('-') + [None, None])[:3]
            browserLanguages.append(unicode(language))

        existingLanguages = []
        for language in browserLanguages:
            if language in application.enabledLanguages:
                existingLanguages.append(language)

        existingLanguages.append(application.defaultLanguage)

        uniqueLanguages = util.uniqify(existingLanguages)

        return uniqueLanguages


class UtilNameShortener(grok.GlobalUtility):
    grok.implements(asmmobile.interfaces.INameShortener)

    def __init__(self, *args, **kw):
        super(UtilNameShortener, self).__init__(*args, **kw)

        import asmmobile.config as config
        if config.mobileMode:
            self.shortener = util.NameShortener()
        else:
            self.shortener = util.AsIsName()

    def shorten(self, name):
        return self.shortener.shorten(name)


class MobileTemplateFactory(grok.GlobalUtility):
    grok.implements(grokcore.view.interfaces.ITemplateFileFactory)
    grok.name('ptm')

    def __call__(self, filename, _prefix=None):
        return asmmobile.components.MobileTemplate(filename=filename, _prefix=_prefix)


class StylesheetTemplateFactory(grok.GlobalUtility):
    grok.implements(grokcore.view.interfaces.ITemplateFileFactory)
    grok.name('css')

    def __call__(self, filename, _prefix=None):
        import asmmobile.config as config

        cleaner = None
        if config.mobileMode:
            shortener = zope.component.getUtility(asmmobile.interfaces.INameShortener)
            cleaner = asmmobile.components.CssWhitespaceCleaner(shortener)

        return asmmobile.components.CssTemplate(
            filename=filename, _prefix=_prefix, cleaner=cleaner)


class ImportError(RuntimeError):
    def __init__(self, msg):
        self.msg = msg


DATE_FORMAT_RE = re.compile(ur"^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d\d\d$")

class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(interfaces.IAsmMobile, interfaces.IEventOwner)

    navigationName = _(u"Home")

    importConfig = u""

    notices = 'notices'

    enabledLanguages = []

    enableInternalization = True

    defaultLanguage = 'test'

    languageCookie = 'l'

    def _initialize(config):
        cls = AsmMobile
        cls.partyName = config.partyName
        cls.locations = config.locations
        cls.events = config.events

    util.runDeferred(_initialize)

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        defaultLanguage = self.defaultLanguage

        locations = asmmobile.location.LocalizedLocationContainer()
        self[self.locations] = locations
        locations[defaultLanguage] = asmmobile.location.LocationContainer()

        events = asmmobile.event.LocalizedEventContainer()
        self[self.events] = events
        events[defaultLanguage] = asmmobile.event.EventContainer()


    @property
    def EVENTS(self):
        return self[self.events]


    @property
    def LOCATIONS(self):
        return self[self.locations]

    def _getLanguagedEvents(self, request):
        defaultEvents = self.EVENTS[self.defaultLanguage]
        events = self.EVENTS.get(request.locale.id.language, defaultEvents)
        return events

    def getFirstEvent(self, request):
        events = self._getLanguagedEvents(request)
        return events.firstEvent


    def getLastEvent(self, request):
        events = self._getLanguagedEvents(request)
        return events.lastEvent


    def updateLocations(self, languagedLocations):
        if self.defaultLanguage not in languagedLocations:
            raise ImportError("No locations for default language.")

        locationData = {}
        for language, locations in languagedLocations.items():
            locationData[language] = {}
            for location, locationValues in locations.items():
                locationId = str(location)
                if locationId not in languagedLocations[self.defaultLanguage]:
                    raise ImportError("All locations must be available for default language.")
                locationUnicodeValues = util.unicodefyStrDict(locationValues)
                locationData[language][locationId] = locationUnicodeValues

        # Make sure that every language has all locations.
        defaultLocations = locationData[self.defaultLanguage]
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

        # Remove unused languages.
        for language in self.LOCATIONS.keys():
            if language not in locationData:
                del self.LOCATIONS[language]

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

        if 'start-original' in values and not DATE_FORMAT_RE.match(values['start-original']):
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
        if 'start-original' in eventValues:
            eventValues['start-original'] = dateutil.parser.parse(eventValues['start-original'])
        eventValues['end'] = dateutil.parser.parse(eventValues['end'])

        return eventValues

    def updateEvents(self, languagedEvents):
        if self.defaultLanguage not in languagedEvents:
            raise ImportError("No events for default language.")

        eventData = {}

        # Check for event sanity and objectify textual location data.
        for language, events in languagedEvents.items():
            locations = self.LOCATIONS[language]
            eventData[language] = {}
            for event, values in events.items():
                if event not in languagedEvents[self.defaultLanguage]:
                    raise ImportError("All events must be available for default language.")

                eventId = str(event)
                eventValues = self._sanitizeEvent(locations, values)
                eventData[language][eventId] = eventValues

        # Make sure that all languages have at least some version of all events.
        for eventId, values in eventData[self.defaultLanguage].items():
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
                del self.EVENTS[language]


    def getEvents(self, request, eventFilter=None):
        events = self._getLanguagedEvents(request)
        return events.getEvents(eventFilter)

    def getLastModified(self, request):
        events = self._getLanguagedEvents(request)
        return events.lastModified


nextSelectors = [selector.FutureEvents()]

def _initializeSelectors(config):
    global nextSelectors

    for selectString in config.selectNextEvents.split("&"):
        selectParts = selectString.split(":", 1)
        selectName = selectParts[0]
        if len(selectParts) != 2:
            selectArgs = None
        else:
            selectArgs = selectParts[1]
        nextSelectors.append(selector.types[selectName].construct(selectArgs))

util.runDeferred(_initializeSelectors)


def getSorter(sorterString):
    sorters = sorterString.split("&")
    sorter = orderby.types[sorters[0]]
    decorators = sorters[1:]
    for decorator in decorators:
        parts = decorator.split(":", 1)
        name = parts[0]
        if len(parts) != 2:
            args = None
        else:
            args = parts[1]
        sorter = orderby.decorators[name](sorter, args)
    return sorter

currentSort = None
nextSort = None

def _initializeSorters(config):
    global currentSort
    currentSort = getSorter(config.sortCurrentEvents)
    global nextSort
    nextSort = getSorter(config.sortNextEvents)

util.runDeferred(_initializeSorters)


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
        nextSelector = selector.AndSelector(nextSelectors)
        nextEvents = filter(nextSelector, notEndedEvents)
        nextEvents.sort(nextSort)

        self.nextEvents = getEventList(self, nextEvents)

        changedSelector = selector.AndSelector(
            [selector.StartTimeChangedEvents(),
             selector.NotHiddenOriginalEvents().reset(now)])
        changedEvents = filter(changedSelector, notEndedEvents)
        self.changedEvents = getEventList(self, changedEvents)


    def _getPartyStatus(self, now, nextEvents):
        firstEvent = self.context.getFirstEvent(self.request)
        lastEvent = self.context.getLastEvent(self.request)

        hasUpcomingEvents = len(nextEvents) > 0
        haveEvents = (firstEvent.id != u'')
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
    grok.viewletmanager(asmmobile.components.NavigationManager)
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
            links.append("<a href='%s'>%s</a>" % (
                    self.view.url(context, aliasFor), cgi.escape(name)))

        currentName = translate(
            contexts[-1].navigationName, context=self.request)
        links.append("%s" % cgi.escape(currentName))

        return self.BREADCRUMB_SEPARATOR.join(links)


class Layout(MobileView):
    """The view that contains the main layout."""
    grok.context(zope.interface.Interface)

    def _initialize(config):
        cls = Layout
        cls.sourceUrl = config.sourceUrl
        cls.siteName = config.siteName
        cls.mainSiteUrl = config.mainSiteUrl
        cls.pageLocations = (_(u"Locations"), AsmMobile.locations, None)

    util.runDeferred(_initialize)

    pageOverview = (_(u"Home"), '', None)
    pageAllEvents = (_(u"All events"), 'all#now', 'head-navigation')
    pageAbout = (_(u"About"), 'about', None)


class LayoutStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.components.StylesheetManager)
    grok.context(zope.interface.Interface)
    grok.order(1)


class ScheduleChangedStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.components.StylesheetManager)
    grok.context(AsmMobile)
    grok.view(Index)
    grok.order(2)

    displayStyle = False

    def update(self):
        if len(self.view.changedEvents) > 0:
            self.displayStyle = True


class Favicon(MobileView):
    grok.context(zope.interface.Interface)

    grok.name("favicon.ico")
    template = None

    def _initialize(config):
        cls = Favicon
        cls.cacheTime = util.defaultCacheTime(config)

    util.runDeferred(_initialize)

    def update(self):
        # XXX a horrible hack to go around Grok 1.3 static resource behaviour
        # changes.
        self.redirect(self.static.get("favicon.ico")())

    def render(self):
        return ''


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
    grok.viewletmanager(asmmobile.components.StylesheetManager)
    grok.context(interfaces.IAsmMobile)
    grok.view(AllEvents)
    grok.order(2)

#import pdb; pdb.set_trace()

class About(MobileView):
    grok.context(interfaces.IAsmMobile)

    def _initialize(config):
        cls = About
        cls.cacheTime = util.defaultCacheTime(config)

    util.runDeferred(_initialize)

    qrCodeAltTemplate = _(u"QR code link to home page (%s).")

    def update(self):
        self.qrCodeAlt = translate(
            self.qrCodeAltTemplate, context=self.request) % self.application_url()


class ErrorLayout(MobileView):
    """The view that contains the error layout."""
    grok.context(zope.interface.Interface)

    def _initialize(config):
        cls = ErrorLayout
        cls.siteName = config.siteName

    util.runDeferred(_initialize)

import zope.errorview.browser

class Error401Unauthorized(MobileView, zope.errorview.browser.UnauthorizedView):
    grok.context(IUnauthorized)
    grok.name('index.html')

    def update(self):
        self.siteUrl = self.url(grok.getSite())
        zope.errorview.browser.UnauthorizedView.update(self)

class Error404NotFound(MobileView):
     grok.context(INotFound)
     grok.name('index.html')

     def update(self):
         self.siteUrl = self.url(grok.getSite())
         self.response.setStatus(404)


class Error500InternalServerError(MobileView):
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
        application = grok.getApplication()
        if language is not None:
            self.request.response.setCookie(
                application.languageCookie, language, path='/')

        self.redirect(util.findReturnTo(self))

    def render(self):
        return ''


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")

    grok.context(interfaces.IAsmMobile)
    form_fields = grok.AutoFields(interfaces.IAsmMobile)

    @grok.action("Save changes")
    def saveChanges(self, **kw):
        # import pdb; pdb.set_trace()
        # if self.context.locations != kw['locations']
        oldEvents = self.context.events
        oldLocations = self.context.locations
        self.applyData(self.context, **kw)
        if kw['events'] != oldEvents:
            self.context[kw['events']] = self.context[oldEvents]
            del self.context[oldEvents]
        if kw['locations'] != oldLocations:
            self.context[kw['locations']] = self.context[oldLocations]
            del self.context[oldLocations]

        self.redirect(self.url(self.context, 'edit'))


def setupObjectInputWidget(field, request):
    factory = zope.component.getUtility(zope.component.interfaces.IFactory,
                                        name=field.schema.__name__)
    return zope.formlib.objectwidget.ObjectWidget(field, request, factory)

class LanguageChoice(persistent.Persistent):

    zope.interface.implements(interfaces.ILanguageChoice)
