import zope.interface

class ITransmogrifier(zope.interface.Interface):
    """The transmogrifier transforms objects through a pipeline"""
    
    context = zope.interface.Attribute("The targeted IFolderish context")
    
    def __call__(self, configuration_id, **overrides):
        """Load and execute the named pipeline configuration
        
        Any dictionaries passed in as extra keywords, are interpreted as
        section configuration overrides. Only string keys and values are
        accepted.
        
        """
        
    def __getitem__(section):
        """Retrieve a section from the pipeline configuration"""
        
    def keys():
        """List all sections in the pipeline configuration"""
        
    def __iter__():
        """Iterate over all the section names in the pipeline configuration"""


class ISectionBlueprint(zope.interface.Interface):
    """Blueprints create pipe sections"""
    
    def __call__(transmogrifier, name, options, previous):
        """Create a named pipe section for a transmogrifier
        
        Returns an ISection with the given name and options, which will
        use previous as an input iterator when iterated over itself.
        
        """

class ISection(zope.interface.Interface):
    """A section in a transmogrifier pipe"""
    
    def __iter__():
        """Pipe sections are iterables.
        
        During iteration they process the previous section to produce output
        for the next pipe section.
        
        """
