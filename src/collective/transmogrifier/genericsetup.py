"""Generic setup integration"""
from zope.annotation.interfaces import IAnnotations
from interfaces import ITransmogrifier

IMPORT_CONTEXT = 'collective.transmogrifier.genericsetup.import_context'

def importTransmogrifier(context):
    """Run named transmogrifier pipelines read from transmogrifier.txt

    Pipeline identifiers are read one per line; empty lines and those starting
    with a # are skipped.

    """
    data = context.readDataFile('transmogrifier.txt')
    if not data:
        return

    transmogrifier = ITransmogrifier(context.getSite())
    anno = IAnnotations(transmogrifier)
    anno[IMPORT_CONTEXT] = context
    logger = context.getLogger('collective.transmogrifier.genericsetup')

    for pipeline in data.splitlines():
        pipeline = pipeline.strip()
        if not pipeline or pipeline[0] == '#':
            continue
        logger.info('Running transmogrifier pipeline %s' % pipeline)
        transmogrifier(pipeline)
        logger.info('Transmogrifier pipeline %s complete' % pipeline)

    del anno[IMPORT_CONTEXT]
