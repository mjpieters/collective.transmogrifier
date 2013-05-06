import logging

from lxml import etree
from lxml import html

from zope.interface import classProvides
from zope.interface import implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression


class XMLWalkerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    xpath = "@href | @src"
    prefix = 'element-'

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.logger = logging.getLogger(name)

        self.trees = Expression(
            options.get('trees', "python:item.get('_trees', ())"),
            transmogrifier, name, options)

        self.cache = options.get('cache', 'false').lower() == 'true'
        self.seen = set()

        # By default, insert matching elements
        self.xpath = options.get('xpath', self.xpath)
        self.elementkey = Expression(
            options.get('key', 'nothing'), transmogrifier, name, options)

        # By default, insert references to parent items
        self.parentkey = Expression(
            options.get('parent-key', 'string:_parent'),
            transmogrifier, name, options)

        # By default, only insert a type for folders
        self.typekey = Expression(
            options.get('type-key', "string:_type"),
            transmogrifier, name, options)
        self.typevalue = Expression(
            options.get('type-value', "string:Folder"),
            transmogrifier, name, options)

        # By default yield default pages for folders
        #   but do not keep references to child items
        self.defaultpagekey = Expression(
            options.get('default-page-key', 'nothing'),
            transmogrifier, name, options)
        self.isdefaultpagekey = Expression(
            options.get('is-default-page-key', 'string:_is_defaultpage'),
            transmogrifier, name, options)
        self.childrenkey = Expression(
            options.get('children-key', 'nothing'),
            transmogrifier, name, options)

        self.keys = [
            (key, Expression(options[self.prefix + key],
                             transmogrifier, name, options))
            for key in options.get('element-keys', '').splitlines() if key]

    def __iter__(self):
        for item in self.previous:
            trees = self.trees(item) or ()
            if trees:
                # get everything we need from the item before yielding
                elementkey = self.elementkey(item)
                parentkey = self.parentkey(item)
                childrenkey = self.childrenkey(item)

            yield item

            if not isinstance(trees, (list, tuple)):
                trees = [trees]
            for tree in trees:
                if not (
                    callable(getattr(tree, 'read', None))
                    or isinstance(tree, etree.ElementBase)):
                    tree = html.fragment_fromstring(
                        tree, create_parent=True)
                if self.cache:
                    tree_string = etree.tostring(tree)
                    if tree_string in self.seen:
                        self.logger.info('Skipping already seen tree')
                        continue
                    self.seen.add(tree_string)
                for child_item in self.walk(
                    item, tree, elementkey, parentkey, childrenkey):
                    yield child_item

    def walk(self, item, tree, elementkey, parentkey, childrenkey):
        depth = 0
        parents = [(depth, item, tree)]
        for event, element in etree.iterwalk(tree, events=("start", "end")):
            if event == 'end':
                if element.xpath(self.xpath):
                    previous_depth, previous, previous_element = parents[-1]
                    if previous_depth == 0:
                        pass
                    elif depth > previous_depth:
                        # Previous item has children, item is a folder

                        # Maybe insert a default page item
                        isdefaultpagekey = self.isdefaultpagekey(previous)
                        if isdefaultpagekey:
                            defaultpage = previous.copy()
                            defaultpage[isdefaultpagekey] = True
                            if parentkey:
                                defaultpage[parentkey] = previous

                            defaultpagekey = self.defaultpagekey(previous)
                            if defaultpagekey:
                                previous[defaultpagekey] = defaultpage

                            if childrenkey:
                                previous.setdefault(
                                    childrenkey, []).append(defaultpage)

                        # Maybe insert a type for the folder
                        typekey = self.typekey(previous)
                        if typekey:
                            typevalue = self.typevalue(previous)
                            if typevalue:
                                previous[typekey] = typevalue

                        # Add option keys
                        previous.update(
                            (key, expression(
                                previous, element=previous_element,
                                tree_item=item, tree=tree))
                            for key, expression in self.keys)

                        yield previous
                        if isdefaultpagekey:
                            # Add option keys
                            defaultpage.update(
                                (key, expression(
                                    defaultpage, element=previous_element,
                                    tree_item=item, tree=tree))
                                for key, expression in self.keys)

                            yield defaultpage
                    else:
                        # Previous item had no children

                        # Add option keys
                        previous.update(
                            (key, expression(
                                previous, element=previous_element,
                                tree_item=item, tree=tree))
                            for key, expression in self.keys)

                        yield previous

                    while depth <= parents[-1][0]:
                        # We have stepped out/up a level
                        parents.pop()

                    # Assemble child item
                    child = {}
                    if elementkey:
                        child[elementkey] = element
                    parent = parents[-1][1]
                    if parentkey:
                        child[parentkey] = parent
                    if childrenkey:
                        parent.setdefault(childrenkey, []).append(child)

                    parents.append((depth, child, element))

                depth -= 1
            else:
                depth += 1

        previous_depth, previous, previous_element = parents[-1]
        if previous_depth != 0:
            # Add option keys
            previous.update(
                (key, expression(previous, element=previous_element,
                                 tree_item=item, tree=tree))
                for key, expression in self.keys)

            yield previous
