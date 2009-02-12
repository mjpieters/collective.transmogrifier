from zope.configuration.fields import MessageID
from zope.configuration.fields import Path
from zope.configuration.fields import PythonIdentifier
from zope.interface import Interface

from transmogrifier import configuration_registry

#### transmogrifier:registerConfig

class IRegisterConfigDirective(Interface):

    """Register pipeline configurations with the global registry.
    """

    name = PythonIdentifier(
        title=u'Name',
        description=u"If not specified 'default' is used.",
        default=u'default',
        required=False)

    title = MessageID(
        title=u'Title',
        description=u'Optional title for the pipeline configuration.',
        default=None,
        required=False)

    description = MessageID(
        title=u'Description',
        description=u'Optional description for the pipeline configuration.',
        default=None,
        required=False)

    configuration = Path(
        title=u'Configuration',
        description=u"The pipeline configuration file to register.",
        required=True)


_configuration_regs = []
def registerConfig(_context, configuration, name=u'default', title=None,
                   description=None):
    """Add a new configuration to the registry"""
    if title is None:
        title = u"Pipeline configuration '%s'" % name

    if description is None:
        description = u''

    _configuration_regs.append('%s' % name)

    _context.action(
        discriminator=('registerConfig', name),
        callable=configuration_registry.registerConfiguration,
        args=(name, title, description, configuration))
