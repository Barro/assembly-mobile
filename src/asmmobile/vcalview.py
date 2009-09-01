import datetime
import grok

from asmmobile.components import MobileView
import asmmobile.interfaces as interfaces
import asmmobile.util as util

class EventOwnerWrapper(object):
    def __init__(self, contentType, events):
        self.contentType = contentType
        self.events = events


class ICalendarWrapper(grok.View):
    """The view that contains the iCalendar events."""
    grok.context(EventOwnerWrapper)


class ICalendar(MobileView):
    """The view that contains the iCalendar events."""

    template = None

    grok.context(EventOwnerWrapper)
    grok.name("index.html")

    cacheTime = util.AddTime(datetime.timedelta(minutes=15))

    def update(self):
        self.response.setHeader('Content-Type', self.context.contentType)

    def render(self):
        page = ICalendarWrapper(self.context, self.request)
        page.events = self.context.events
        page.now = self.now
        return page().replace("\n", "\r\n")


class EventCalendarTraverser(grok.Traverser):
    grok.context(interfaces.IEventOwner)

    def traverse(self, name):
        if name.endswith('.vcs'):
            return EventOwnerWrapper("text/x-vCalendar", self.context.events)
        elif name.endswith('.ics'):
            return EventOwnerWrapper("text/calendar", self.context.events)


class ICalTimeView(grok.View):
    grok.context(datetime.datetime)
    grok.name("ical")

    def render(self):
        return self.context.strftime('%Y%m%dT%H%M%S')
