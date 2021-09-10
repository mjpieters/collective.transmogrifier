# -*- coding: utf-8 -*-
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
        title=u"Name",
        description=u"If not specified 'default' is used.",
        default="default",
        required=False,
    )

    title = MessageID(
        title=u"Title",
        description=u"Optional title for the pipeline configuration.",
        default=None,
        required=False,
    )

    description = MessageID(
        title=u"Description",
        description=u"Optional description for the pipeline configuration.",
        default=None,
        required=False,
    )

    configuration = Path(
        title=u"Configuration",
        description=u"The pipeline configuration file to register.",
        required=True,
    )


_configuration_regs = []


def registerConfig(
    _context, configuration, name="default", title=None, description=None
):
    """Add a new configuration to the registry"""
    if title is None:
        title = u"Pipeline configuration '%s'" % name

    if description is None:
        description = u""

    _configuration_regs.append("%s" % name)

    _context.action(
        discriminator=("registerConfig", name),
        callable=configuration_registry.registerConfiguration,
        args=(name, title, description, configuration),
    )
