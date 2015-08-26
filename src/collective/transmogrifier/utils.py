import os.path
import posixpath
import re
import sys
import pprint
from logging import getLogger, DEBUG

from zope.component import getUtility
try:
    from zope.pagetemplate import engine
except ImportError:
    # BBB: Zope 2.10
    from zope.app.pagetemplate import engine

from interfaces import ISection
from interfaces import ISectionBlueprint


def openFileReference(transmogrifier, ref):
    """
    Get an open file handle in one of the following forms:

    * importcontext:file.txt
    * dotted.package:file.txt
    * /file/system/file.txt

    Where "importcontext:" means find the file in the GS import context.
    Return None if there was no file to be found
    """
    if ref.startswith('importcontext:'):
        try:
            from collective.transmogrifier.genericsetup import IMPORT_CONTEXT
            from zope.annotation.interfaces import IAnnotations
            context = IAnnotations(transmogrifier).get(IMPORT_CONTEXT, None)
            (subdir, filename) = os.path.split(ref.replace('importcontext:', ''))
            if subdir == '':
                # Subdir of '' results import contexts looking for a ''
                # directory I think
                subdir = None
            if hasattr(context, "openDataFile"):
                return context.openDataFile(filename, subdir=subdir)
            if hasattr(context, "readDataFile"):
                import StringIO
                return StringIO.StringIO(
                    context.readDataFile(filename, subdir=subdir))
        except ImportError:
            return None
    # Either no import context or not there.
    filename = resolvePackageReferenceOrFile(ref)
    if os.path.isfile(filename):
        return open(filename, 'r')
    return None


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


def pathsplit(path, ospath=posixpath):
    dirname, basename = ospath.split(path)
    if dirname == ospath.sep:
        yield dirname
    elif dirname:
        for elem in pathsplit(dirname):
            yield elem
        yield basename
    elif basename:
        yield basename


def traverse(context, path, default=None):
    """Resolve an object without acquisition or views."""
    for element in pathsplit(path.strip(posixpath.sep)):
        if not hasattr(context, '_getOb'):
            return default
        context = context._getOb(element, default=default)
        if context is default:
            break
    return context


def constructPipeline(transmogrifier, sections, pipeline=None):
    """Construct a transmogrifier pipeline
    
    ``sections`` is a list of pipeline section ids. Start the pipeline with
    ``pipeline``, or if that's None, with an empty iterator.
    
    """
    if pipeline is None:
        pipeline = iter(())  # empty starter section

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
        pipeline = iter(pipeline)  # ensure you can call .next()

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
        '_'.join(parts),                  # _blueprint_section_key or _blueprint_section
        '_'.join(parts[:2] + parts[3:]),  # _blueprint_key or _blueprint
        '_'.join(parts[:1] + parts[2:]),  # _section_key or _section
    )
    if key is not None:
        keys += ('_'.join(parts[:1] + parts[3:]),)  # _key
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
                expr = lambda x, y = expr: x == y
            self.expressions.append(expr)

    def __call__(self, *values):
        for expr in self.expressions:
            for value in values:
                match = expr(value)
                if match:
                    return value, match
        return None, False


def pformat_msg(obj):
    msg = pprint.pformat(obj)
    if '\n' in msg:
        msg = '\n' + '\n'.join(
            '  ' + line for line in msg.splitlines())
    return msg


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
        logger_base = getattr(transmogrifier, 'configuration_id',
                              'transmogrifier')
        self.logger = getLogger(logger_base + '.' + name)

    def __call__(self, item, **extras):
        extras.update(self.extras)
        result = self.expression(engine.TrustedEngine.getContext(
            item=item,
            transmogrifier=self.transmogrifier,
            name=self.name,
            options=self.options,
            nothing=None,
            modules=sys.modules,
            **extras
        ))
        if self.logger.isEnabledFor(DEBUG):
            formatted = pformat_msg(result)
            self.logger.debug('Expression returned: %s', formatted)
        return result


class Condition(Expression):
    """A transmogrifier condition expression
    
    Test if a pipeline item matches the given TALES expression.
    
    """

    def __call__(self, item, **extras):
        return bool(super(Condition, self).__call__(item, **extras))


def wrapped_tarball(export_context, context):
    """
    Return a tarball, created as an export context, for download

    Usage exmaple:

      transmogrifier(...)
      for info in transmogrifier.get_info('export_context', short=True):
	  # there should be exactly one:
	  return wrapped_tarball(info['context'], self.context)
    """
    result = _export_result_dict(export_context)
    RESPONSE = context.REQUEST.RESPONSE
    RESPONSE.setHeader('Content-type', 'application/x-gzip')
    RESPONSE.setHeader('Content-disposition',
                       'attachment; filename=%s' % result['filename'])
    return result['tarball']


def _export_result_dict(context, steps=None, messages=None):
    """
    Return a dictionary, like returned by SetupTool._doRunExportSteps
    (Products/GenericSetup/tool.py)

    context -- an *export* context!

    (helper for --> wrapped_tarball)
    """
    return {'steps': steps,
            'messages': messages,
            'tarball': context.getArchive(),
            'filename': context.getArchiveFilename()}


def name_and_length(key, val):
    """
    Helper for the itemInfo functions (created by make_itemInfo)

    >>> name_and_length('key', 'value')
    'key (5)'
    """
    if isinstance(val, basestring):
        L = len(val)
        return '%s (%d)' % (key, L)
    elif isinstance(val, (int, float, bool)):
        return '%s=%r' % (key, val)
    else:
        try:
            clsname = val.__class__.__name__
        except AttributeError:
            clsname = None
        return '%s (%s)' % (key, clsname)


def make_itemInfo(name, *values_of, **kwargs):
    """
    For development: create a function which prints a short information about
    the given item.

    >>> itemInfo = make_itemInfo('example', '_path')
    >>> item = dict(_type='text/plain', _path='path/to/item', _other='foo')
    >>> itemInfo(item)
    [example], item #1:
        _path='path/to/item'
        other keys: _other (3), _type (10)
    True

    The futher calls won't print anything ...

    >>> itemInfo(item)
    False

    ... unless shownext or showone options are used.
    """
    data = {'cnt': 0,
            'prefix': '[%(name)s], item #%%d:' % locals(),
            'shownext': 0,
            'showkeys': set(),
            'shown': set(),
            }
    summary_formatter = kwargs.pop('summary_formatter', name_and_length)
    if kwargs.pop('debug', False):
        import pdb
        pdb.set_trace()  # make_itemInfo
    if kwargs:
        raise ValueError('Unsupported keyword arguments: %s' % kwargs)
    if not values_of:
        values_of = [('_path',), ('_type',)]

    def itemInfo(item, shownext=None, showone=None, trace=False):
        """
        Print a short info about the given item; by default, only for the first.

        shownext -- a number >= 0; show the next <shownext> items, including this one
        showone -- a string; show the item in this iteration (in the following
                   iterations, this key will be consumed)
        trace -- boolean: if true, pdb.set_trace() after printing
                 (no printing -> no set_trace)
        """
        data['cnt'] += 1
        if shownext is not None:
            if not isinstance(shownext, int) or shownext < 0:
                raise ValueError('shownext=%(shownext)r: integer >= 0'
                                 ' expected!' % locals())
            data['shownext'] = shownext
        if showone is not None and showone not in data['showkeys']:
            data['showkeys'].add(showone)
            data['shownext'] += 1
        if data['shownext']:
            data['shownext'] -= 1
        elif data['cnt'] > 1:  # by default only print 1st items
            return False
        print data['prefix'] % data['cnt']
        shadow = dict(item)
        for keyset in values_of:
            if isinstance(keyset, basestring):
                keyset = [keyset]
            for key in keyset:
                if key in shadow:
                    val = shadow.pop(key)
                    print '    %(key)s=%(val)r' % locals()
                    break
        other = sorted(shadow.keys())
        if other:
            print '    other keys: ' + ', '.join([
                summary_formatter(key, shadow[key])
                for key in other
                ])
        if trace:
            import pdb
            pdb.set_trace()
        return True

    return itemInfo


def _dump_section(name, dic, main='blueprint'):
    """
    Return a list of strings, representing a pipeline section;
    a helper for --> dump_sections().

    >>> values = {'blueprint': 'my.example',
    ...           'a-boolean': 'false'}
    >>> _dump_section('example', values)
    ['[example]', 'blueprint = my.example', 'a-boolean = false']

    The dictionary was not changed or consumed:

    >>> sorted(values.values())
    [('a-boolean', 'false'), ('blueprint', 'my.example')]
    """
    res = ['[%s]' % name]
    keys = sorted([key for key in dic.keys()
                   if key != main
                   ])
    keys.insert(0, main)
    for key in keys:
        try:
            val = dic[key]
        except KeyError:
            # can happen for main key only
            res.append('# !! No %s value!' % (main,))
        else:
            try:
                val = val.strip()
                if '\n' in val:
                    res.append(key + ' =')
                    for s in filter(None, val.splitlines()):
                        res.append('   '+s)
                else:
                    res.append('%s = %s' % (key, val))
            except (AttributeError, TypeError):
                res.append('%s = %r' % (key, val))
    return res


def dump_sections(dic, joiner='\n'):
    """
    Return a dump of the given transmogrifier configuration (_raw attribute)

    Will handle non-string values gracefully; such values can't be specified in
    a configuration file, though.

    The result is a string which could be written to a configuration file;
    the sections are written in pipeline order.
    Unused sections are skipped.
    """
    res = []
    sections = None
    try:
        tm = dic['transmogrifier']
    except KeyError:
        res.append('# !! No [transmogrifier] section!')
    else:
        try:
            sections = filter(None, tm.get('pipeline').splitlines())
        except KeyError:
            res.append('# !! [transmogrifier] section lacks pipeline value!')
        res.extend(_dump_section('transmogrifier', tm, 'pipeline'))
    res.append('')
    if sections is None:
        sections = sorted([k for k in dic.keys()
                           if k != 'transmogrifier'
                           ])
    for section in sections:
        try:
            secdict = dic[section]
        except KeyError:
            res.append('# !! [%s] section missing!')
        else:
            res.extend(_dump_section(section, secdict))
        res.append('')

    if joiner is None:
        return res
    return joiner.join(res)
