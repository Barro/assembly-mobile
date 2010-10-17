#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2010  Assembly Organizing
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

import cgi
import datetime

import grok
from zope.app.publication.interfaces import IBeforeTraverseEvent
from zope.publisher.browser import applySkin
from zope.i18n import translate
import zope.interface

import asmmobile.interfaces as interfaces
import asmmobile.util as util
import asmmobile.components

COOKIE_SKIN = "s"
SKINS = {}
SKIN_DEFAULT = None

def _initialize(config):
    global SKIN_DEFAULT
    SKIN_DEFAULT = config.skinDefault

util.runDeferred(_initialize)


def addSkin(name, displayName, cls):
    SKINS[name] = (displayName, cls)


@grok.subscribe(interfaces.IAsmMobile, IBeforeTraverseEvent)
def handle(obj, event):
    skin = event.request.cookies.get(COOKIE_SKIN, SKIN_DEFAULT)

    if skin in SKINS:
        displayName, cls = SKINS[skin]
        applySkin(event.request, cls)


class SetSkin(asmmobile.components.MobileView):
    grok.context(zope.interface.Interface)
    grok.name('s')

    template = None

    cacheTime = util.AddTime(datetime.timedelta(seconds=0))

    def publishTraverse(self, request, name):
        self.newSkin = name
        request.setTraversalStack([])
        return self

    def update(self):
        skin = self.newSkin
        if skin is not None:
            self.request.response.setCookie(
                's', skin, path='/')

        self.redirect(util.findReturnTo(self))

    def render(self):
        return ''


class SkinManager(grok.ViewletManager):
    grok.name('skin')
    grok.context(zope.interface.Interface)

    def render(self):
        result = ""
        for viewlet in self.viewlets:
            content = viewlet.render()
            if len(content):
                skinUrl = self.view.urlVR("@@s/%s" % viewlet.name)
                result += "<!---->&#8226;<!----> <a href='%s'>%s</a>" % (
                    cgi.escape(skinUrl), cgi.escape(content))
        return result


class AlternativeSkin(grok.Viewlet):
    grok.viewletmanager(SkinManager)
    grok.context(zope.interface.Interface)

    def _initialize(config):
        cls = AlternativeSkin
        cls.skinAlternative = config.skinAlternative
        cls.name = config.skinAlternative

    util.runDeferred(_initialize)

    def render(self):
        skin = self.skinAlternative

        if skin in SKINS:
            displayName, cls = SKINS[skin]
            return translate(displayName, context=self.request)

        return ''
