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
import asmmobile.config as config

def strip_whitespace_filter_factory(global_conf, strip_types=''):
    def filter(app):
        return StripWhitespaceFilter(app, strip_types=strip_types)
    return filter


def nothing_filter_factory(global_conf):
    return NothingFilter


def mobile_filter_factory(global_conf, filter_types=''):
    if config.mobileMode:
        return strip_whitespace_filter_factory(global_conf, filter_types)
    else:
        return nothing_filter_factory(global_conf)


def strip_headers_filter_factory(global_conf, headers=''):
    headerList = [x.strip().lower() for x in headers.split(" ")]
    headerList = filter(lambda x : len(x) > 0, headerList)
    def header_filter(app):
        return StripHeadersFilter(app, headers=headerList)
    return header_filter


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
        resultStr = re.sub("<!--[^-].*?-->", "", resultStr)
        resultStr = re.sub("( *\n *)+", " ", resultStr)
        resultStr = re.sub("> +", ">", resultStr)
        resultStr = re.sub(" +<", "<", resultStr)
        resultStr = re.sub(" +/>", "/>", resultStr)
        # Add spaces.
        resultStr = re.sub("<!---->", " ", resultStr)

        return [resultStr].__iter__()

class StripWhitespaceFilter(object):
    """This filter strips white space characters from resulting XHTML output
    document.
    """

    def __init__(self, application, strip_types=''):
        self.application = application
        self.stripTypes = strip_types.split()

    def __call__(self, environ, start_response):
        response = StripWhitespaceResponse(start_response, self.stripTypes)
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


class NothingFilter(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)


class StripHeadersFilter(object):
    def __init__(self, app, headers):
        self.app = app
        self.headers = set(headers)

    def __call__(self, environ, start_response):
        def filterHeaders(status, headers, exc_info=None):
            out_headers = []
            for key, value in headers:
                if key.lower() in self.headers:
                    continue
                out_headers.append((key, value))
            return start_response(status, out_headers, exc_info)
        return self.app(environ, filterHeaders)
