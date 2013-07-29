import grok

from asmmobile.tools.update_schedule import updateSchedule


class UpdateScheduleApp(grok.Application):
    enableInternalization = False
    defaultLanguage = "en"
    sendCachingHeaders = False


class UpdateSchedule(grok.Model):
    pass


class Index(grok.View):
    grok.context(UpdateSchedule)

    def update(self):
        asmmobile = __import__("asmmobile")
        config = getattr(asmmobile.tools, 'import-config')
        updateSchedule(self.context.__parent__, config)

    def render(self):
        return "OK"


class BaseTraverser(grok.Traverser):
    grok.context(UpdateScheduleApp)

    def traverse(self, name):
        site = grok.getSite()
        root = site.__parent__
        if name in root:
            scheduleUpdater = UpdateSchedule()
            scheduleUpdater.__name__ = name
            scheduleUpdater.__parent__ = root[name]
            return scheduleUpdater
        return None
