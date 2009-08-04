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

    def mobileUpdate(self):
        self.now = datetime.datetime(2009, 8, 7, 18, 3)

        self.request.response.setHeader("Content-Type", "text/html; charset=UTF-8")
        nextMinute = _TIME_FACTORY.utcnow()
        maxAge = 60 - nextMinute.second%60
        nextMinute += datetime.timedelta(seconds=(maxAge))
        self.request.response.setHeader(
            "Expires", nextMinute.strftime("%a, %d %b %Y %H:%M:%S +0000"))
        self.request.response.setHeader("Cache-Control", "max-age=%d" % maxAge)


    def getTime(self):
        timeFormat = "%Y-%m-%d %H:%M %z"
        return _(u"Current time: %s" % self.now.strftime(timeFormat))


    def getCss(self):
        fp = open("src/asmmobile/static/asmmobile.css", "r")
        compressed = fp.read()
        fp.close()
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed

    def applicationRelativeUrl(self, name):
        return asmmobile.util.applicationRelativeUrl(self, name)


def strip_filter_factory(global_conf, **local_conf):
    def filter(app):
        return StripFilter(app)
    return filter

class StripWhitespaceResponse(object):

    def __init__(self, start_response):
        self.doProcessing = False
        self.start_response = start_response

    def initial_decisions(self, status, headers, exc_info=None):
        contentType = None

        out_headers = []

        for name,value in headers:
            keyName = name.lower()
            if keyName == 'content-type':
                contentType = value
            elif keyName == 'content-length':
                # Ignore content length header for server recalculation.
                continue
            out_headers.append((name, value))

        self.doProcessing = False
        if (contentType is not None
            and contentType.lower().startswith("text/html")):
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

    def __init__(self, application):
        self.application = application


    def __call__(self, environ, start_response):
        response = StripWhitespaceResponse(start_response)
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


class ICalendarWrapper(grok.View):
    """The view that contains the iCalendar events."""
    grok.context(zope.interface.Interface)


class ICalendar(MobileView):
    """The view that contains the iCalendar events."""
    grok.context(zope.interface.Interface)

    def update(self):
        self.mobileUpdate()
        self.response.setHeader('Content-Type', "text/calendar")

    def render(self):
        page = ICalendarWrapper(self.context, self.request)
        page.events = self.events
        page.now = self.now
        return page().replace("\n", "\r\n")


