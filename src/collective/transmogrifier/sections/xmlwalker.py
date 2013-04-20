from lxml import etree
from lxml import html

from zope.interface import classProvides
from zope.interface import implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Expression


class XMLWalkerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    xpath = "@href"

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.treeskey = defaultMatcher(options, 'trees-key', name, 'trees')

        self.xpathkey = defaultMatcher(options, 'xpath-key', name, 'xpath')
        self.xpath = options.get('xpath', self.xpath)
        self.elementkey = Expression(
            options.get('key', 'string:_element'),
            transmogrifier, name, options)

        self.parentkey = Expression(
            options.get('parent-key', 'string:_parent'),
            transmogrifier, name, options)
        self.childrenkey = Expression(
            options.get('children-key', 'nothing'),
            transmogrifier, name, options)

    def __iter__(self):
        for item in self.previous:
            treeskey = self.treeskey(*item)[0]
            if treeskey:
                # get everything we need from the item before yielding
                trees = item[treeskey]
                parentkey = self.parentkey(item)
                elementkey = self.elementkey(item)
                childrenkey = self.childrenkey(item)

                # let the item though the pipeline
                yield item

                if not isinstance(trees, list):
                    trees = [trees]
                for tree in trees:
                    if not (
                        callable(getattr(tree, 'read', None))
                        or isinstance(tree, etree.ElementBase)):
                        tree = html.fromstring(tree)
                    for child_item in self.walk(
                        item, tree, parentkey, elementkey, childrenkey):
                        yield child_item

            else:
                # no tree to walk
                yield item

    def walk(self, item, tree, parentkey, elementkey, childrenkey):
        depth = 0
        parents = [(depth, item)]
        for event, element in etree.iterwalk(tree, events=("start", "end")):
            if event == 'end':
                if element.xpath(self.xpath):
                    previous_depth, previous = parents[-1]
                    if previous is item:
                        pass
                    elif depth > previous_depth:
                        # Previous item has children
                        defaultpage = previous.copy()
                        if childrenkey:
                            previous[childrenkey] = [defaultpage]
                        defaultpage[parentkey] = previous
                        yield previous
                        yield defaultpage
                    else:
                        # Previous item had no children
                        yield previous

                    while depth <= parents[-1][0]:
                        # We have stepped out/up a level
                        parents.pop()

                    # Assemble child item
                    parent = parents[-1][1]
                    child = {parentkey: parent,
                             elementkey: element}
                    if childrenkey:
                        parent.setdefault(childrenkey, []).append(child)

                    parents.append((depth, child))

                depth -= 1
            else:
                depth += 1

        previous_depth, previous = parents[-1]
        if previous is not item:
            yield previous
