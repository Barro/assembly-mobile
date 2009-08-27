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
import re

import grok
import zope.interface

import asmmobile.util

_TIME_FACTORY = datetime.datetime(2000, 1, 1)


class MobileView(grok.View):
    grok.context(zope.interface.Interface)

    cacheTime = asmmobile.util.ceilToNextMinute

    contentType = "application/xhtml+xml; charset=UTF-8"

    cssDirectory = "src/asmmobile/static"
    cssFiles = ["asmmobile.css"]

    def __call__(self, *args, **kw):
        self.request.response.setHeader(
            "Content-Type",
            self.contentType
            )

        self.now = _TIME_FACTORY.now()

        utcnow = _TIME_FACTORY.utcnow()
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


    def getTime(self):
        timeFormat = "%Y-%m-%d %H:%M %z"
        return _(u"Current time: %s" % self.now.strftime(timeFormat))


    def getCss(self):
        cssData = ""
        for filename in self.cssFiles:
            fp = open("%s/%s" % (self.cssDirectory , filename), "r")
            cssData += fp.read()
            fp.close()

        compressed = cssData
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed


    def urlR(self, target=None):
        return asmmobile.util.applicationRelativeUrl(self, target)

    def application_urlR(self, target="."):
        return asmmobile.util.applicationRelativeUrl(self, target)


def strip_filter_factory(global_conf, strip_types=''):
    def filter(app):
        return StripFilter(app, strip_types=strip_types)
    return filter


class StripWhitespaceResponse(object):

    def __init__(self, start_response, stripTypes):
        self.doProcessing = False
        self.start_response = start_response
        self.stripTypes = stripTypes

    def initial_decisions(self, status, headers, exc_info=None):
        contentType = None

        out_headers = []

        for name,value in headers:
            keyName = name.lower()
            if keyName == 'content-type':
                contentType = value.split(";")[0].lower()
            elif keyName == 'content-length':
                # Ignore content length header for server recalculation.
                continue
            out_headers.append((name, value))

        self.doProcessing = False
        if contentType in self.stripTypes:
            self.doProcessing = True

        if self.doProcessing:
            headers = out_headers
        return self.start_response(status, headers, exc_info)

    def finish_response(self, app_iter):
        if not app_iter:
            return app_iter

        resultStr = "".join(app_iter)
        # Filter out white space and comments.
        resultStr = re.sub("<!--.*?-->", "", resultStr)
        resultStr = re.sub("( *\n *)+", " ", resultStr)
        resultStr = re.sub(" +/>", "/>", resultStr)

        return [resultStr].__iter__()

class StripFilter(object):
    """This filter strips white space characters from resulting XHTML output
    document.
    """

    def __init__(self, application, strip_types=''):
        self.application = application
        self.stripTypes = strip_types.split()

    def __call__(self, environ, start_response):
        response = StripWhitespaceResponse(start_response,
                                           self.stripTypes)
        app_iter = self.application(environ, response.initial_decisions)
        if response.doProcessing:
            app_iter = response.finish_response(app_iter)
        return app_iter


    def getHeader(self, headerName):
        for key,value in self.headers_out:
            if key.lower() == headerName:
                return value
        return None


    def __iter__(self):
        result = self.app(self.env, self.start_response)
        resultIter  = result.__iter__()

        filterContent = True
        contentType = self.getHeader('content-type')
        # If result is not text/html, return immediately
        if (contentType is None \
                or not contentType.lower().startswith("text/html")):
            self.real_start(self.status, self.headers_out, self.exc_info)
            return resultIter

        resultStr = "".join(resultIter)

        # Filter out white space and comments.
        resultStr = re.sub("<!--.*?-->", "", resultStr)
        resultStr = re.sub("( *\n *)+", " ", resultStr)
        resultStr = re.sub(" +/>", "/>", resultStr)

        headers_out = []
        for key,value in self.headers_out:
            if key.lower() == 'content-length':
                value = len(resultStr)
            headers_out.append((key,value))

        self.real_start(self.status, headers_out, self.exc_info)

        return [resultStr].__iter__()
