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

import dateutil.tz
import cgi
import os
import re
import urllib
import urlparse


import grok
import grokcore.view.components
import grokcore.view.interfaces
import zope.component
from zope.i18n import translate
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.interface import Interface
import zope.tales.expressions
from zope.tales.interfaces import ITALESExpression

import asmmobile.util as util
import asmmobile.interfaces as interfaces

UNIQUE_VAR_NAME = 'u'
RANDOM_REDIRECT_BYTES = 4

# XXX replace this with utility.
def uniqueIdGenerator():
    return os.urandom(RANDOM_REDIRECT_BYTES).encode("hex")
UNIQUE_ID_GENERATOR = uniqueIdGenerator

class MobileView(grok.View):
    grok.context(Interface)

    cacheTime = util.ceilToNextMinute

    charset = "UTF-8"
    contentType = "application/xhtml+xml;charset=%s" % charset

    @property
    def language(self):
        return self.request.locale.id.language

    @property
    def availableLanguages(self):
        application = grok.getApplication()
        if application.enableInternalization:
            return application.enabledLanguages
        return [application.defaultLanguage]

    skin = None

    def _sendCachingHeaders(self):
        utcnow = self.now.astimezone(dateutil.tz.tzutc())
        cacheTime = self.cacheTime(utcnow)

        if cacheTime == util.INTERVAL_ZERO_SECONDS:
            return

        expiresAt = utcnow + cacheTime

        self.request.response.setHeader(
            "Expires",
            expiresAt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )
        self.request.response.setHeader(
            "Cache-Control",
            "max-age=%d,public" % (cacheTime.seconds + cacheTime.days * 86400)
            )
        self.request.response.setHeader(
            'Vary',
            "Accept-Encoding,Accept-Language,Cookie"
            )

    def _sendDisableCachingHeaders(self):
        self.request.response.setHeader(
            'Cache-Control',
            "no-cache"
            )

    def __call__(self, *args, **kw):
        self.now = util.clock()

        # We are calling this here because the first setupLocale() call in
        # zope.publisher.http.HTTPRequest does not include application and
        # therefore we can't actually determine what locales are available.
        self.request.setupLocale()

        self.request.response.setHeader(
            "Content-Type",
            self.contentType
            )

        try:
            application = grok.getApplication()
        except:
            application = None

        if application is not None and application.sendCachingHeaders:
            self._sendCachingHeaders()
        else:
            self._sendDisableCachingHeaders()


        return super(MobileView, self).__call__(*args, **kw)


    def urlVR(self, target=""):
        if not self.request._endswithslash:
            if self.__name__ == 'index':
                return "%s/%s" % (self.context.__name__, target)
            else:
                return "%s/%s" % (self.__name__, target)
        else:
            return target


    def urlR(self, target=""):
        if not self.request._endswithslash and self.__name__ == 'index':
            return "%s/%s" % (self.context.__name__, target)
        else:
            return target


    def application_urlR(self, target=""):
        return util.applicationRelativeUrl(self, target)


    def redirectUnique(self, target):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(target)

        queryDict = cgi.parse_qs(query, True)
        queryDict[UNIQUE_VAR_NAME] = UNIQUE_ID_GENERATOR()
        query = urllib.urlencode(queryDict)

        self.redirect(urlparse.urlunparse((scheme, netloc, path, params, query, fragment)))


class MobileTemplate(grokcore.view.components.PageTemplate):

    def render(self, view):
        return super(MobileTemplate, self).render(view).encode(view.charset)


class ShortenExpression(object):
    grok.implements(ITALESExpression)

    def __init__(self, name, expr, engine):
        self._s = expr
        shortener = zope.component.getUtility(interfaces.INameShortener)
        self._short = shortener.shorten(self._s)

    def __call__(self, econtext):
        return self._short

    def __str__(self):
        return 'shortened expression (%s)' % `self._s`

    def __repr__(self):
        return '<ShortenExpression %s>' % `self._s`


class CssNoneCleaner(object):
    def __call__(self, data):
        return data


class CssWhitespaceCleaner(object):
    commentMatch = re.compile(r"/\*.*?\*/", re.DOTALL)
    newlinesMatch = re.compile(r" *\n *")
    separatorMatch = re.compile(r" *([,:\{;]) *")
    semicolonMatch = re.compile(r";\}")

    def __init__(self, nameShortener):
        self.shortener = nameShortener

    def removeExtraContent(self, content):
        compressed = content
        compressed = self.commentMatch.sub("", compressed)
        compressed = self.newlinesMatch.sub("", compressed)
        compressed = self.separatorMatch.sub(r"\1", compressed)
        compressed = self.semicolonMatch.sub("}", compressed)
        return compressed

    def minifySelector(self, selectorString):
        selectors = selectorString.split(",")
        result = []
        for selector in selectors:
            parts = selector.split(" ")
            selectorResult = []
            for part in parts:
                if "." in part:
                    left, right = part.split(".", 1)
                    right = self.shortener.shorten(right)
                    part = "%s.%s" % (left, right)
                elif "#" in part:
                    left, right = part.split("#", 1)
                    right = self.shortener.shorten(right)
                    part = "%s#%s" % (left, right)
                selectorResult.append(part)
            result.append(" ".join(selectorResult))
        return ",".join(result)

    def __call__(self, content):
        compressed = self.removeExtraContent(content)
        selectors = compressed.split("{")
        outputSelectors = []
        for selector in selectors:
            selectorData = selector.split("}")
            selectorData[-1] = self.minifySelector(selectorData[-1])
            outputSelectors.append("}".join(selectorData))
        return "{".join(outputSelectors)


class StylesheetManager(grok.ViewletManager):
    grok.name('stylesheets')
    grok.context(Interface)


class AlertStylesheetManager(grok.ViewletManager):
    grok.name('alert-stylesheet')
    grok.context(Interface)


class AlertStylesheet(grok.Viewlet):
    grok.viewletmanager(AlertStylesheetManager)
    grok.context(Interface)


class CssTemplate(grokcore.view.components.PageTemplate):

    def __init__(self, string=None, filename=None, _prefix=None, cleaner=None):
        super(CssTemplate, self).__init__(string=string, filename=filename, _prefix=_prefix)

        if cleaner == None:
            self.cleaner = CssNoneCleaner()
        else:
            self.cleaner = cleaner

    def render(self, view):
        return self.cleaner(super(CssTemplate, self).render(view))


from zope.publisher.defaultview import getDefaultViewName

class ContentTraverser(grok.Traverser):
    grok.context(interfaces.ILocalizedContentContainer)

    def traverse(self, name):
        content = self.getContent(self.request)
        return content.get(name, None)

    def getContent(self, request):
        # Somehow we don't have application when the request (traversing) starts
        # but we need the current language here and behold! We have the
        # application here.
        languages = zope.component.getAdapter(request, IUserPreferredLanguages)
        content = None
        for language in languages.getPreferredLanguages():
            if language in self.context:
                content = self.context[language]
                break

        if content is None:
            content = self.context[grok.getApplication().defaultLanguage]

        return content

    def browserDefault(self, request):
        # content = self.getContent(request)
        content = self.context
        view_name = getDefaultViewName(content, request)
        view_uri = "@@%s" % view_name
        return content, (view_uri,)

#     def publishTraverse(self, request, name):
#         content = self.getContent(request)
#         print self.context
#         print name
#         print content
#         view = zope.component.queryMultiAdapter((content, request))
#         return view.publishTraverse(request, name)

class ViewLink(grok.View):
    grok.context(tuple)
    grok.name("viewlink")

    def render(self):
        pageName, pageLocation, cssStyles = self.context
        location = pageLocation
        if hasattr(pageLocation, "__call__"):
            location = pageLocation(self.context)

        nohashPart = location.split("#", 1)[0]
        cleanedViewUrl = self.request.getURL().replace("/@@index", "")
        styles = ''
        if cssStyles is not None:
            shortener = zope.component.getUtility(interfaces.INameShortener)
            styles = " class='%s'" % " ".join(map(shortener.shorten, cssStyles.split(" ")))

        if self.application_url(nohashPart) == cleanedViewUrl:
            return "<strong%s>%s</strong>" % (styles, translate(
                pageName, context=self.request))

        locationUrl = util.applicationRelativeUrl(self, location)
        return '<a href="%s"%s>%s</a>' % (
            locationUrl, styles, translate(pageName, context=self.request))


class QrCodeLink(grok.View):
    """Generates links that point to QR codes generated by Google Charts API.

    There is qrencode Python module that also generates QR codes but it fails
    to generate proper QR codes with longer strings.
    """

    grok.context(str)
    grok.name("qrcodeurl")

    chartLink = u"http://chart.apis.google.com/chart?chs=%(chartSize)s&cht=qr&chl=%(data)s"

    chartSize = "320x320"

    def render(self):

        chartLink = self.chartLink % {
            'data': urllib.quote_plus(self.context),
            'chartSize': self.chartSize,
            }

        return chartLink


class NavigationManager(grok.ViewletManager):
    grok.name('navigation')
    grok.context(Interface)


class Domain(grok.View):
    grok.context(unicode)

    startPart = 0

    def render(self):
        components = urlparse.urlparse(self.context)
        domain = components.netloc.split(":")[0]
        secondary_level_domain = ".".join(domain.split(".")[self.startPart:])
        return secondary_level_domain

class MainDomain(Domain):
    grok.context(unicode)

    startPart = -2


class DescriptionEscape(grok.View):
    grok.context(unicode)

    def render(self):
        result = re.sub("\n\n+", "</p><p>", self.context)
        return result
