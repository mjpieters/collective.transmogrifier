from zope.component import getUtility
from interfaces import ISection
from interfaces import ISectionBlueprint

def constructPipeline(transmogrifier, sections, pipeline=None):
    if pipeline is None:
        pipeline = iter(()) # empty starter section
    
    for section_id in sections:
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
