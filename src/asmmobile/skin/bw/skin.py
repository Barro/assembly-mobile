import grok
import asmmobile.app
import asmmobile.interfaces
import zope.interface

class BwSkin(grok.IDefaultBrowserLayer):
    grok.skin("bw")

class LayoutStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.app.StylesheetManager)
    grok.context(zope.interface.Interface)
    grok.layer(BwSkin)

class NextEventsStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.app.StylesheetManager)
    grok.context(asmmobile.interfaces.IAsmMobile)
    grok.view(asmmobile.app.NextEvents)
    grok.layer(BwSkin)
