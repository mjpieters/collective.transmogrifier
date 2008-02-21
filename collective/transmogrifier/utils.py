import re
import sys

from zope.component import getUtility
from zope.app.pagetemplate import engine

from interfaces import ISection
from interfaces import ISectionBlueprint

def constructPipeline(transmogrifier, sections, pipeline=None):
    """Construct a transmogrifier pipeline
    
    ``sections`` is a list of pipeline section ids. Start the pipeline with
    ``pipeline``, or if that's None, with an empty iterator.
    
    """
    if pipeline is None:
        pipeline = iter(()) # empty starter section
    
    for section_id in sections:
        section_id = section_id.strip()
        if not section_id:
            continue
        section_options = transmogrifier[section_id]
        blueprint_id = section_options['blueprint'].decode('ascii')
        blueprint = getUtility(ISectionBlueprint, blueprint_id)
        pipeline = blueprint(transmogrifier, section_id, section_options, 
                             pipeline)
        if not ISection.providedBy(pipeline):
            raise ValueError('Blueprint %s for section %s did not return '
                             'an ISection' % (blueprint_id, section_id))
        pipeline = iter(pipeline) # ensure you can call .next()
    
    return pipeline

class Matcher(object):
    """Given a set of string expressions, return the first match.
    
    Normally items are matched using equality, unless the expression
    starts with re: or regexp:, in which case it is treated as a regular
    expression.
    
    Regular expressions will be compiled and applied in match mode
    (matching anywhere in the string).
    
    """
    def __init__(self, *expressions):
        self.expressions = []
        for expr in expressions:
            expr = expr.strip()
            if not expr:
                continue
            if expr.startswith('re:') or expr.startswith('regexp:'):
                expr = expr.split(':', 2)[1]
                expr = re.compile(expr).match
            else:
                expr = lambda x, y=expr: x == y
            self.expressions.append(expr)
    
    def __call__(self, value):
        for expr in self.expressions:
            match = expr(value)
            if match:
                return match
        return False

class Expression(object):
    """A transmogrifier expression
    
    Evaluate the expression with a transmogrifier context.
    
    """
    def __init__(self, expression, transmogrifier, name, options, **extras):
        self.expression = engine.Engine.compile(expression)
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.extras = extras

    def __call__(self, item, **extras):
        extras.update(self.extras)
        return self.expression(engine.Engine.getContext(
            item = item,
            transmogrifier = self.transmogrifier,
            name = self.name,
            options = self.options,
            nothing = None,
            modules = sys.modules,
            **extras
        ))

class Condition(Expression):
    """A transmogrifier condition expression
    
    Test if a pipeline item matches the given TALES expression.
    
    """
    def __call__(self, item):
        return bool(super(Condition, self).__call__(item))
