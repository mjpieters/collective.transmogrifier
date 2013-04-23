import logging

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

        self.logger = logging.getLogger(name)

        self.treeskey = defaultMatcher(options, 'trees-key', name, 'trees')
        self.trees = set()

        # By default, insert matching elements
        self.xpath = options.get('xpath', self.xpath)
        self.elementkey = Expression(
            options.get('key', 'string:_element'),
            transmogrifier, name, options)

        # By default, insert references to parent items
        self.parentkey = Expression(
            options.get('parent-key', 'string:_parent'),
            transmogrifier, name, options)

        # By default, only insert a type for folders
        self.typekey = Expression(
            options.get('type-key',
                        "python:'_defaultpage' in item and '_type'"),
            transmogrifier, name, options)
        self.typevalue = Expression(
            options.get('type-value', "string:Folder"),
            transmogrifier, name, options)

        # By default yield default pages for folders
        #   but do not keep references to child items
        self.defaultpagekey = Expression(
            options.get('default-page-key', 'string:_defaultpage'),
            transmogrifier, name, options)
        self.childrenkey = Expression(
            options.get('children-key', 'nothing'),
            transmogrifier, name, options)

    def __iter__(self):
        for item in self.previous:
            yielded_item = False

            treeskey = self.treeskey(*item)[0]
            if treeskey:
                # get everything we need from the item before yielding
                trees = item[treeskey]
                elementkey = self.elementkey(item)
                parentkey = self.parentkey(item)
                childrenkey = self.childrenkey(item)

                if not isinstance(trees, list):
                    trees = [trees]
                for tree in trees:
                    if not (
                        callable(getattr(tree, 'read', None))
                        or isinstance(tree, etree.ElementBase)):
                        tree = html.fromstring(tree)
                    tree_string = etree.tostring(tree)
                    if tree_string in self.trees:
                        self.logger.info(
                            'Skipping already seen tree in %r', treeskey)
                        continue
                    self.trees.add(tree_string)
                    for child_item in self.walk(
                        item, tree, elementkey, parentkey, childrenkey):
                        if not yielded_item and child_item is item:
                            yield item
                            yielded_item = True
                        else:
                            yield child_item

            if not yielded_item:
                # no tree to walk
                yield item

    def walk(self, item, tree, elementkey, parentkey, childrenkey):
        depth = 0
        parents = [(depth, item)]
        for event, element in etree.iterwalk(tree, events=("start", "end")):
            if event == 'end':
                if element.xpath(self.xpath):
                    previous_depth, previous = parents[-1]
                    if depth > previous_depth:
                        # Previous item has children, item is a folder

                        # Maybe insert a default page item
                        defaultpagekey = self.defaultpagekey(
                            previous, tree_item=item)
                        if defaultpagekey:
                            defaultpage = previous.copy()
                            if parentkey:
                                defaultpage[parentkey] = previous

                            previous[defaultpagekey] = defaultpage
                            if childrenkey:
                                previous.setdefault(
                                    childrenkey, []).append(defaultpage)

                        # Maybe insert a type for the folder
                        typekey = self.typekey(previous, tree_item=item)
                        if typekey:
                            typevalue = self.typevalue(
                                previous, tree_item=item)
                            if typevalue:
                                previous[typekey] = typevalue

                        yield previous
                        yield defaultpage
                    else:
                        # Previous item had no children
                        yield previous

                    while depth <= parents[-1][0]:
                        # We have stepped out/up a level
                        parents.pop()

                    # Assemble child item
                    child = {elementkey: element}
                    parent = parents[-1][1]
                    if parentkey:
                        child[parentkey] = parent
                    if childrenkey:
                        parent.setdefault(childrenkey, []).append(child)

                    # Maybe insert a type
                    typekey = self.typekey(previous, tree_item=item)
                    if typekey:
                        typevalue = self.typevalue(
                            previous, tree_item=item)
                        if typevalue:
                            previous[typekey] = typevalue

                    parents.append((depth, child))

                depth -= 1
            else:
                depth += 1

        previous_depth, previous = parents[-1]
        if previous is not item:
            yield previous
