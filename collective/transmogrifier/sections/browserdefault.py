from zope.interface import classProvides, implements
from zope.component import queryUtility

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.CMFDynamicViewFTI.interface import ISelectableBrowserDefault


class BrowserDefaultSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        if 'layout-key' in options:
            layoutkeys = options['layout-key'].splitlines()
        else:
            layoutkeys = defaultKeys(options['blueprint'], name, 'layout')
        self.layoutkey = Matcher(*layoutkeys)
        if 'default-page-key' in options:
            defaultpagekeys = options['default-page-key'].splitlines()
        else:
            defaultpagekeys = defaultKeys(options['blueprint'], name, 'defaultpage')
        self.defaultpagekey = Matcher(*defaultpagekeys)

    def __iter__(self):
        defered_links = []
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            if not pathkey:
                yield item; continue

            layoutkey = self.layoutkey(*item.keys())[0]
            defaultpagekey = self.defaultpagekey(*item.keys())[0]

            path = item[pathkey]

            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:
                yield item; continue

            if not ISelectableBrowserDefault.providedBy(obj):
                yield item; continue

            if layoutkey:
                layout = item[layoutkey]
                obj.setLayout(layout)

            if defaultpagekey:
                defaultpage = item[defaultpagekey]
                obj.setDefaultPage(defaultpage)

            yield item
