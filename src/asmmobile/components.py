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
from grokcore.view.components import PageTemplate
import zope.app.pagetemplate.engine
import zope.component
from zope.i18n import translate
from zope.interface import Interface
import zope.tales.expressions
from zope.tales.interfaces import ITALESExpression

import asmmobile.util as util
import asmmobile.interfaces as interfaces

RANDOM_REDIRECT_BYTES = 4

class MobileView(grok.View):
    grok.context(Interface)

    cacheTime = util.ceilToNextMinute

    charset = "UTF-8"
    contentType = "application/xhtml+xml;charset=%s" % charset

    language = None

    skin = None

    def _initialize(config):
        cls = MobileView
        cls.enableInternalization = config.enableInternalization
        cls.sendCachingHeaders = config.sendCachingHeaders

    util.runDeferred(_initialize)

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

    def _setupLanguages(self):
        self.language = self.request.locale.id.language

    def __call__(self, *args, **kw):
        self.now = util.clock()

        if self.enableInternalization:
            self._setupLanguages()

        self.request.response.setHeader(
            "Content-Type",
            self.contentType
            )

        if self.sendCachingHeaders:
            self._sendCachingHeaders()

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
        queryDict['u'] = os.urandom(RANDOM_REDIRECT_BYTES).encode("hex")
        query = urllib.urlencode(queryDict)

        self.redirect(urlparse.urlunparse((scheme, netloc, path, params, query, fragment)))


class MobileTemplate(PageTemplate):

    def render(self, view):
        return super(MobileTemplate, self).render(view).encode(view.charset)

SHORTENER = None

def _initializeShortener(config):
    global SHORTENER
    if config.mobileMode:
        SHORTENER = util.NameShortener()
    else:
        SHORTENER = util.AsIsName()

util.runDeferred(_initializeShortener)


class ShortenExpr(object):
    grok.implements(ITALESExpression)

    def __init__(self, name, expr, engine):
        self._s = expr
        self._short = SHORTENER.shorten(self._s)

    def __call__(self, econtext):
        return self._short

    def __str__(self):
        return 'shortened expression (%s)' % `self._s`

    def __repr__(self):
        return '<ShortenExpr %s>' % `self._s`


# Registering handler for "shorten" type.
zope.app.pagetemplate.engine.TrustedEngine.registerType("shorten", ShortenExpr)


class TimeFormatExpr(object):
    grok.implements(ITALESExpression)

    def __init__(self, name, expr, engine):
        format, pathExpr = expr.split(",", 1)
        self._s = expr
        self._format = format
        self._path = zope.tales.expressions.PathExpr("", pathExpr, engine)

    def __call__(self, econtext):
        formatter = econtext.request.locale.dates.getFormatter("dateTime")
        formatter.setPattern(self._format)
        return formatter.format(self._path(econtext))

    def __str__(self):
        return 'formatter expression (%s)' % `self._s`

    def __repr__(self):
        return '<TimeFormatExpr %s>' % `self._s`

# Registering handler for "timeformat" type.
zope.app.pagetemplate.engine.TrustedEngine.registerType("timeformat", TimeFormatExpr)


class StylesheetManager(grok.ViewletManager):
    grok.name('stylesheets')
    grok.context(Interface)

    commentMatch = re.compile(r"/\*.*?\*/", re.DOTALL)
    newlinesMatch = re.compile(r" *\n *")
    separatorMatch = re.compile(r" *([,:\{;]) *")
    semicolonMatch = re.compile(r";\}")

    def _initialize(config):
        cls = StylesheetManager
        cls.mobileMode = config.mobileMode

    util.runDeferred(_initialize)

    def minifySelector(self, selectorString):
        selectors = selectorString.split(",")
        result = []
        for selector in selectors:
            parts = selector.split(" ")
            selectorResult = []
            for part in parts:
                if "." in part:
                    left, right = part.split(".", 1)
                    right = SHORTENER.shorten(right)
                    part = "%s.%s" % (left, right)
                elif "#" in part:
                    left, right = part.split("#", 1)
                    right = SHORTENER.shorten(right)
                    part = "%s#%s" % (left, right)
                selectorResult.append(part)
            result.append(" ".join(selectorResult))
        return ",".join(result)

    def removeExtraContent(self, content):
        compressed = content
        compressed = self.commentMatch.sub("", compressed)
        compressed = self.newlinesMatch.sub("", compressed)
        compressed = self.separatorMatch.sub(r"\1", compressed)
        compressed = self.semicolonMatch.sub("}", compressed)
        return compressed

    def render(self):
        content = super(StylesheetManager, self).render()

        if not self.mobileMode:
            return content

        compressed = self.removeExtraContent(content)
        selectors = compressed.split("{")
        outputSelectors = []
        for selector in selectors:
            selectorData = selector.split("}")
            selectorData[-1] = self.minifySelector(selectorData[-1])
            outputSelectors.append("}".join(selectorData))
        return "{".join(outputSelectors)


from zope.app.publisher.browser import getDefaultViewName

class ContentTraverser(grok.Traverser):
    grok.context(interfaces.ILocalizedContentContainer)

    def _initialize(config):
        cls = ContentTraverser
        cls.defaultLanguage = config.defaultLanguage

    util.runDeferred(_initialize)

    def traverse(self, name):
        content = self.getContent(self.request)
        return content.get(name, None)

    def getContent(self, request):
        content = self.context.get(request.locale.id.language, None)
        if content is None:
            content = self.context[self.defaultLanguage]
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
        pageName, pageLocation = self.context
        nohashPart = pageLocation.split("#", 1)[0]
        cleanedViewUrl = self.request.getURL().replace("@@index", "")
        if self.application_url(nohashPart) == cleanedViewUrl:
            return "<strong>%s</strong>" % translate(
                pageName, context=self.request)

        locationUrl = util.applicationRelativeUrl(self, pageLocation)
        return '<a href="%s">%s</a>' % (
            locationUrl, translate(pageName, context=self.request))


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
