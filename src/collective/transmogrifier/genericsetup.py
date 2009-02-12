"""Generic setup integration"""
from interfaces import ITransmogrifier

def importTransmogrifier(context):
    """Run named transmogrifier pipelines read from transmogrifier.txt
    
    Pipeline identifiers are read one per line; empty lines and those starting
    with a # are skipped.
    
    """
    data = context.readDataFile('transmogrifier.txt')
    if not data:
        return
    
    transmogrier = ITransmogrifier(context.getSite())
    logger = context.getLogger('collective.transmogrifier.genericsetup')
    
    for pipeline in data.splitlines():
        pipeline = pipeline.strip()
        if not pipeline or pipeline[0] == '#':
            continue
        logger.info('Running transmogrier pipeline %s' % pipeline)
        transmogrier(pipeline)
        logger.info('Transmogrifier pipeline %s complete' % pipeline)
