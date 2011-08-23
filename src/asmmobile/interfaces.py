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

from zope.component import queryUtility
from zope.i18n.interfaces import ITranslationDomain
import zope.interface
import zope.schema
from zope import schema
import zc.sourcefactory.contextual

from asmmobile import AsmMobileMessageFactory as _

class INavigationObject(zope.interface.Interface):
    navigationName = schema.TextLine(title=u"Name")


class LanguageSource(zc.sourcefactory.contextual.BasicContextualSourceFactory):

    def getValues(self, context):
        translationDomain = queryUtility(ITranslationDomain, _._domain)
        languages = translationDomain.getCatalogsInfo().keys()
        return map(str, languages)


class ILanguageChoice(zope.interface.Interface):
    languageName = zope.schema.Set(
        title=u'Language name',
        )

    id = zope.schema.TextLine(
        title=u'Language code',
        description=u'Language code.')


class IAsmMobile(INavigationObject):
    """Marker interface for the application object."""

    importConfig = schema.Text(title=u"Import configuration", required=False)

    locations = schema.TextLine(title=u"Locations path name", required=True)

    events = schema.TextLine(title=u"Events path name", required=True)

    notices = schema.TextLine(
        title=u"Notice path name",
        description=u"Notices are short messages that are shown to user at certain time.",
        required=True,
        )

    languageCookie = schema.TextLine(
        title=u"Language cookie name",
        description=u"Cookie that is used to determine user's language.",
        required=True)

    defaultLanguage = schema.Choice(
        title=u"Default Language",
        required=True,
        source=LanguageSource())

    enableInternalization = schema.Bool(title=u"Enable internalization")

    enabledLanguages = zope.schema.List(
        title=u"Enabled languages",
        value_type=schema.Choice(source=LanguageSource())
        )

    # enabledLanguages = schema.TextLine(
    #     title=u"Enabled languages",
    #     description=u"List of enabled languages.",
    #     required=False)

    def updateLocations(locations):
        pass

    def updateEvents(events):
        pass

    def getEvents(request, eventFilter=None):
        pass


class IEventOwner(zope.interface.Interface):

    def getLastModified(request):
        pass

    def getEvents(request):
        pass


class IEventContainer(zope.interface.Interface):
    lastModified = zope.interface.Attribute(
        u"When any event has last been modified"
        )

    def updateEvents(values):
        pass

    def getEvents(eventFilter):
        """Returns a list of events filtered through eventFilter function.

        Events are given for filter function in ascending start time order.
        """


class IEvent(INavigationObject):
    lastModified = zope.interface.Attribute(
        u"When this event has last been modified"
        )

    id = zope.interface.Attribute("")

    name = schema.TextLine(title=u"Name")

    # XXX: max_length=config.shortNameMaximumLength
    shortName = schema.TextLine(
        title=u"Short name", max_length=50)

    start = schema.Datetime(title=u"Start time")

    # Original start time that can be used to create notices about schedule
    # changes.
    startOriginal = schema.Datetime(
        title=u"Original start time", required=False)

    end = schema.Datetime(title=u"End time")

    # XXX schema.URI has bugs and we can't use it.
    url = schema.TextLine(title=u"External URL", required=False)
    isMajor = schema.Bool(title=u"Is major event")
    categories = zope.interface.Attribute("")
    description = schema.Text(title=u"Description", required=False)

    location = zope.interface.Attribute("")
    majorLocation = zope.interface.Attribute("")



class ILocationContainer(zope.interface.Interface):
    def updateLocations(locationValues):
        pass


class ILocation(INavigationObject):

    id = zope.interface.Attribute("")
    name = schema.TextLine(title=u"Name")
    # XXX schema.URI has bugs.
    url = schema.TextLine(title=u"URL", required=False)

    description = schema.Text(title=u"Description")

    majorLocation = zope.interface.Attribute("")
    priority = schema.Int(title=u"Priority")
    hideUntil = zope.interface.Attribute("")


class ILocalizedContentContainer(INavigationObject):
    def getContent(request):
        pass


class INameShortener(zope.interface.Interface):
    def shorten(name):
        pass
