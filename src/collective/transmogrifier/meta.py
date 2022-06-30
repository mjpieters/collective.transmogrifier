from collective.transmogrifier.transmogrifier import configuration_registry
from zope.configuration.fields import MessageID
from zope.configuration.fields import Path
from zope.interface import Interface
from zope.schema import DottedName


class IRegisterConfigDirective(Interface):
    """Register pipeline configurations with the global registry.

    transmogrifier:registerConfig
    """

    name = DottedName(
        title="Name",
        description="If not specified 'default' is used.",
        default="default",
        required=False,
    )

    title = MessageID(
        title="Title",
        description="Optional title for the pipeline configuration.",
        default=None,
        required=False,
    )

    description = MessageID(
        title="Description",
        description="Optional description for the pipeline configuration.",
        default=None,
        required=False,
    )

    configuration = Path(
        title="Configuration",
        description="The pipeline configuration file to register.",
        required=True,
    )


_configuration_regs = []


def registerConfig(
    _context, configuration, name="default", title=None, description=None
):
    """Add a new configuration to the registry"""
    if title is None:
        title = "Pipeline configuration '%s'" % name

    if description is None:
        description = ""

    _configuration_regs.append("%s" % name)

    _context.action(
        discriminator=("registerConfig", name),
        callable=configuration_registry.registerConfiguration,
        args=(name, title, description, configuration),
    )
