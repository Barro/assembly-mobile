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

import re
import urlparse
import dateutil.tz

from zope.interface import Interface

from grokcore.view.components import PageTemplate

import grok

import asmmobile.util as util
import asmmobile.config as config

class MobileView(grok.View):
    grok.context(Interface)

    cacheTime = util.ceilToNextMinute

    charset = "UTF-8"
    contentType = "application/xhtml+xml; charset=%s" % charset

    def __call__(self, *args, **kw):
        self.request.response.setHeader(
            "Content-Type",
            self.contentType
            )

        self.now = config.clock.now(dateutil.tz.tzlocal())

        utcnow = config.clock.now(dateutil.tz.tzutc())
        cacheTime = self.cacheTime(utcnow)

        expiresAt = utcnow + cacheTime

        self.request.response.setHeader(
            "Expires",
            expiresAt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )
        self.request.response.setHeader(
            "Cache-Control",
            "max-age=%d, public" % (cacheTime.seconds + cacheTime.days * 86400)
            )
        self.request.response.setHeader(
            'Vary',
            "Accept-Encoding"
            )

        return super(MobileView, self).__call__(*args, **kw)


    def urlR(self, target=""):
        if not self.request._endswithslash and self.__name__ == 'index':
            return "%s/%s" % (self.context.__name__, target)
        else:
            return target


    def application_urlR(self, target=""):
        return util.applicationRelativeUrl(self, target)


class MobileTemplate(PageTemplate):
    def render(self, view):
        return super(MobileTemplate, self).render(view).encode(view.charset)


class StylesheetManager(grok.ViewletManager):
    grok.name('stylesheets')
    grok.context(Interface)

    def render(self):
        compressed = super(StylesheetManager, self).render()
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed
