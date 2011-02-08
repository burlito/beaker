from kid import Element
import turbogears
from turbogears.database import session

def make_link(url, text):
    # make an <a> element
    a = Element('a', {'class': 'list'}, href=turbogears.url(url))
    a.text = text
    return a

def make_edit_link(name, id):
    # make an edit link
    return make_link(url  = 'edit?id=%s' % id,
                     text = name)

def make_remove_link(id):
    # make a remove link
    return make_link(url  = 'remove?id=%s' % id,
                     text = 'Remove (-)')

def make_scan_link(id):
    # make a rescan link
    return make_link(url  = 'rescan?id=%s' % id,
                     text = 'Rescan (*)')

def make_fake_link(name,id,text):
    # make something look like a href
    a  = Element('a')
    a.attrib['class'] = "list"
    a.attrib['style'] = "color:#22437f;cursor:pointer"
    a.attrib['name'] = name
    a.attrib['id'] = id
    a.text = '%s ' % text
    return a

def sqla_cache(f):
    the_cache = {}
    def do_cache(*args):
        args = tuple(args)
        if args in the_cache: #session merge puts object into session
            return session.merge(the_cache[args],dont_load=True)
        else:
            result = f(*args)
            the_cache[args] = result
            return result
    return do_cache

def to_byte_string(encoding):
    """
    encode the dict/array/string returned by generators
    """
    def encode(f):
        def inner(*args, **kw):
            encoded_return = None 
            try:
                result = f(*args, **kw).next() 
                try:
                    encoded_return = {}
                    for k,v in result.items():
                        encoded_return[k] = unicode(v).encode(encoding)
                    yield encoded_return
                except AttributeError, e: 
                    log.debug(e) 
                    try:
                        encoded_return = [unicode(v).encode(encoding) for v in result]
                        yield encoded_return
                    except AttributeError, e: 
                        log.debug(e)
                        yield unicode(result).encode(encoding)
            except AttributeError,e: 
                log.error('Function %s does not implement generator methods. Failed with error: %s' % (f.__name__, e))
                yield None

        return inner
    return encode