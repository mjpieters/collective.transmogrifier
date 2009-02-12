import codecs
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher, Condition

def _get_default_encoding(site):
    from Products.CMFPlone.utils import getSiteEncoding
    return getSiteEncoding(site)

class CodecSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    from_ = None
    from_error_handler = 'strict'
    to = None
    to_error_handler = 'strict'
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        
        if options.get('from'):
            from_ = options['from'].strip().lower()
            if from_ != 'unicode':
                if from_ == 'default':
                    from_ = _get_default_encoding(transmogrifier.context)
                
                # Test if the decoder is available
                codecs.getdecoder(from_)
                
                self.from_ = from_
        
        self.from_error_handler = options.get(
            'from-error-handler', self.from_error_handler).strip().lower()
        # Test if the error handler is available
        codecs.lookup_error(self.from_error_handler)
        
        if options.get('to'):
            to = options['to'].strip().lower()
            if to != 'unicode':
                if to == 'default':
                    to = _get_default_encoding(transmogrifier.context)
                
                # Test if the encoder is available
                codecs.getencoder(to)
                
                self.to = to
        
        self.to_error_handler = options.get(
            'to-error-handler', self.to_error_handler).strip().lower()
        # Test if the error handler is available
        codecs.lookup_error(self.to_error_handler)
        
        self.matcher = Matcher(*options['keys'].splitlines())
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
    
    def __iter__(self):
        from_ = self.from_
        if from_ is None:
            def decode(value):
                if not isinstance(value, unicode):
                    raise ValueError('Not a unicode string: %s' % value)
                return value
        else:
            from_error_handler = self.from_error_handler
            def decode(value):
                return value.decode(from_, from_error_handler)
        
        to = self.to
        if to is None:
            def encode(value):
                if not isinstance(value, unicode):
                    raise ValueError('Not a unicode string: %s' % value)
                return value
        else:
            to_error_handler = self.to_error_handler
            def encode(value):
                return value.encode(to, to_error_handler)
        
        for item in self.previous:
            for key in item:
                match = self.matcher(key)[1]
                if match and self.condition(item, key=key, match=match):
                    item[key] = encode(decode(item[key]))
            yield item
