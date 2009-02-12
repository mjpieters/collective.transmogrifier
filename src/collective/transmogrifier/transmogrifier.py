import re
import ConfigParser
import UserDict

from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.interfaces import IFolderish

from interfaces import ITransmogrifier
from utils import resolvePackageReference, constructPipeline

class ConfigurationRegistry(object):
    def __init__(self):
        self.clear()
    
    def clear(self):
        self._config_info = {}
        self._config_ids = []
    
    def registerConfiguration(self, name, title, description, configuration):
        if name in self._config_info:
            raise KeyError('Duplicate pipeline configuration: %s' % name)
        
        self._config_ids.append(name)
        self._config_info[name] = dict(
            id=name,
            title=title, 
            description=description, 
            configuration=configuration)
            
    def getConfiguration(self, id):
        return self._config_info[id].copy()
        
    def listConfigurationIds(self):
        return tuple(self._config_ids)

configuration_registry = ConfigurationRegistry()

# Test cleanup support
from zope.testing.cleanup import addCleanUp
addCleanUp(configuration_registry.clear)
del addCleanUp


class Transmogrifier(UserDict.DictMixin):
    implements(ITransmogrifier)
    adapts(IFolderish)
    
    def __init__(self, context):
        self.context = context
        
    def __call__(self, configuration_id, **overrides):
        self._raw = _load_config(configuration_id, **overrides)
        self._data = {}
            
        options = self._raw['transmogrifier']
        sections = options['pipeline'].splitlines()
        pipeline = constructPipeline(self, sections)       
        
        # Pipeline execution
        for item in pipeline:
            pass # discard once processed
        
    def __getitem__(self, section):
        try:
            return self._data[section]
        except KeyError:
            pass
        
        # May raise key error
        data = self._raw[section]
        
        options = Options(self, section, data)
        self._data[section] = options
        options._substitute()
        return options

    def __setitem__(self, key, value):
        raise NotImplementedError('__setitem__')

    def __delitem__(self, key):
        raise NotImplementedError('__delitem__')

    def keys(self):
        return self._raw.keys()

    def __iter__(self):
        return iter(self._raw)

class Options(UserDict.DictMixin):
    def __init__(self, transmogrifier, section, data):
        self.transmogrifier = transmogrifier
        self.section = section
        self._raw = data
        self._cooked = {}
        self._data = {}

    def _substitute(self):
        for key, value in self._raw.items():
            if '${' in value:
                self._cooked[key] = self._sub(value, [(self.section, key)])
        
    def get(self, option, default=None, seen=None):
        try:
            return self._data[option]
        except KeyError:
            pass
        
        value = self._cooked.get(option)
        if value is None:
            value = self._raw.get(option)
            if value is None:
                return default
        
        if '${' in value:
            key = self.section, option
            if seen is None:
                seen = [key]
            elif key in seen:
                raise ValueError('Circular reference in substitutions.')
            else:
                seen.append(key)

            value = self._sub(value, seen)
            seen.pop()

        self._data[option] = value
        return value

    _template_split = re.compile('([$]{[^}]*})').split
    _valid = re.compile('\${[-a-zA-Z0-9 ._]+:[-a-zA-Z0-9 ._]+}$').match
    _tales = re.compile('^\s*string:', re.MULTILINE).match
    def _sub(self, template, seen):
        parts = self._template_split(template)
        subs = []
        for ref in parts[1::2]:
            if not self._valid(ref):
                 # A value with a string: TALES expression?
                if self._tales(template):
                    subs.append(ref)
                    continue
                raise ValueError('Not a valid substitution %s.' % ref)
            
            names = tuple(ref[2:-1].split(':'))
            value = self.transmogrifier[names[0]].get(names[1], None, seen)
            if value is None:
                raise KeyError('Referenced option does not exist:', *names)
            subs.append(value)
        subs.append('')

        return ''.join([''.join(v) for v in zip(parts[::2], subs)])
        
    def __getitem__(self, key):
        try:
            return self._data[key]
        except KeyError:
            pass

        v = self.get(key)
        if v is None:
            raise KeyError('Missing option: %s:%s' % (self.section, key))
        return v

    def __setitem__(self, option, value):
        if not isinstance(value, str):
            raise TypeError('Option values must be strings', value)
        self._data[option] = value

    def __delitem__(self, key):
        if key in self._raw:
            del self._raw[key]
            if key in self._data:
                del self._data[key]
            if key in self._cooked:
                del self._cooked[key]
        elif key in self._data:
            del self._data[key]
        else:
            raise KeyError, key

    def keys(self):
        raw = self._raw
        return list(self._raw) + [k for k in self._data if k not in raw]

    def copy(self):
        result = self._raw.copy()
        result.update(self._cooked)
        result.update(self._data)
        return result

def _update_section(section, included):
    """Update section dictionary with included options
    
    Included options are only put into the section if not already defined.
    Section keys ending with + or - are the sum or difference respectively
    of that option and the included options. Note that - options are processed
    before + options.
    
    """
    keys = set(section.keys())
    add = set([k for k in keys if k.endswith('+')])
    remove = set([k for k in keys if k.endswith('-')])
    
    for key in remove:
        option = key.strip(' -')
        if option in keys:
            raise ValueError('Option %s specified twice', option)
        included[option] = '\n'.join([
            v for v in included.get(option, '').splitlines()
            if v and v not in section[key].splitlines()])
        del section[key]
    
    for key in add:
        option = key.strip(' +')
        if option in keys:
            raise ValueError('Option %s specified twice', option)
        included[option] = '\n'.join([
            v for v in included.get(option, '').splitlines() +
                       section[key].splitlines()
            if v])
        del section[key]
    
    included.update(section)
    return included

def _load_config(configuration_id, seen=None, **overrides):
    if seen is None:
        seen = []
    if configuration_id in seen:
        raise ValueError(
            'Recursive configuration extends: %s (%r)' % (
                configuration_id, seen))
    seen.append(configuration_id)
    
    if ':' in configuration_id:
        configuration_file = resolvePackageReference(configuration_id)
    else:
        config_info = configuration_registry.getConfiguration(configuration_id)
        configuration_file = config_info['configuration']
    parser = ConfigParser.RawConfigParser()
    parser.optionxform = str # case sensitive
    parser.readfp(open(configuration_file))
    
    includes = None
    result = {}
    for section in parser.sections():
        result[section] = dict(parser.items(section))
        if section == 'transmogrifier':
            includes = result[section].pop('include', includes)
    
    if includes:
        for configuration_id in includes.split()[::-1]:
            include = _load_config(configuration_id, seen)
            sections = set(include.keys()) | set(result.keys())
            for section in sections:
                result[section] = _update_section(
                    result.get(section, {}), include.get(section, {}))
    
    seen.pop()
    
    for section, options in overrides.iteritems():
        result.setdefault(section, {}).update(options)
    
    return result
