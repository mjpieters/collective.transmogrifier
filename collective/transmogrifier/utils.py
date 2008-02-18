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

    def __call__(self, item):
        return self.expression(engine.Engine.getContext(
            item = item,
            transmogrifier = self.transmogrifier,
            name = self.name,
            options = self.options,
            nothing = None,
            modules = sys.modules,
            **self.extras
        ))

class Condition(Expression):
    """A transmogrifier condition expression
    
    Test if a pipeline item matches the given TALES expression.
    
    """
    def __call__(self, item):
        return bool(super(Condition, self).__call__(item))
