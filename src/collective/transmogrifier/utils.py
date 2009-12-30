import os.path
import re
import sys

from zope.component import getUtility
from zope.app.pagetemplate import engine

from interfaces import ISection
from interfaces import ISectionBlueprint

def resolvePackageReferenceOrFile(reference):
    """A wrapper around def ``resolvePackageReference`` which also work if
    reference is a "plain" filename.
    """
    
    if ':' not in reference:
        return reference
    try:
        return resolvePackageReference(reference)
    except ImportError:
        return reference

def resolvePackageReference(reference):
    """Given a package:filename reference, return the filesystem path
    
    ``package`` is a dotted name to a python package, ``filename`` is assumed
    to be a filename located within the package directory.
    
    """
    package, filename = reference.strip().split(':', 1)
    package = __import__(package, {}, {}, ('*',))
    return os.path.join(os.path.dirname(package.__file__), filename)

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

def defaultKeys(blueprint, section, key=None):
    """Create a set of item keys based on blueprint id, section name and key

    These keys will match more specificly targeted item keys first; first
    _blueprint_section_key, then _blueprint_key, then _section_key, then _key.
    
    key is optional, and when omitted results in _blueprint_section, then
    _blueprint, then _section

    """
    parts = ['', blueprint, section]
    if key is not None:
        parts.append(key)
    keys = (
        '_'.join(parts), # _blueprint_section_key or _blueprint_section
        '_'.join(parts[:2] + parts[3:]), # _blueprint_key or _blueprint
        '_'.join(parts[:1] + parts[2:]), # _section_key or _section
    )
    if key is not None:
        keys += ('_'.join(parts[:1] + parts[3:]),) # _key
    return keys

def defaultMatcher(options, optionname, section, key=None, extra=()):
    """Create a Matcher from an option, with a defaultKeys fallback

    If optionname is present in options, that option is used to create a
    Matcher, with the assumption the option holds newline-separated keys.

    Otherwise, defaultKeys is called to generate a default set of keys
    based on options['blueprint'], section and the optional key. Any
    keys in extra are also considered part of the default keys.

    """
    if optionname in options:
        keys = options[optionname].splitlines()
    else:
        keys = defaultKeys(options['blueprint'], section, key)
        for key in extra:
            keys += (key,)
    return Matcher(*keys)

class Matcher(object):
    """Given a set of string expressions, return the first match.
    
    Normally items are matched using equality, unless the expression
    starts with re: or regexp:, in which case it is treated as a regular
    expression.
    
    Regular expressions will be compiled and applied in match mode
    (matching anywhere in the string).
    
    On calling, returns a tuple of (matched, matchresult), where matched is
    the matched value, and matchresult is either a boolean or the regular
    expression match object. When no match was made, (None, False) is
    returned.
    
    """
    def __init__(self, *expressions):
        self.expressions = []
        for expr in expressions:
            expr = expr.strip()
            if not expr:
                continue
            if expr.startswith('re:') or expr.startswith('regexp:'):
                expr = expr.split(':', 1)[1]
                expr = re.compile(expr).match
            else:
                expr = lambda x, y=expr: x == y
            self.expressions.append(expr)
    
    def __call__(self, *values):
        for expr in self.expressions:
            for value in values:
                match = expr(value)
                if match:
                    return value, match
        return None, False

class Expression(object):
    """A transmogrifier expression
    
    Evaluate the expression with a transmogrifier context.
    
    """
    def __init__(self, expression, transmogrifier, name, options, **extras):
        self.expression = engine.TrustedEngine.compile(expression)
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.extras = extras

    def __call__(self, item, **extras):
        extras.update(self.extras)
        return self.expression(engine.TrustedEngine.getContext(
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
    def __call__(self, item, **extras):
        return bool(super(Condition, self).__call__(item, **extras))
