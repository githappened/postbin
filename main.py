import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from models import Bin

import md5
import os
import re

class MainHandler(webapp.RequestHandler):
    def get(self):
        oldbins = extract_postbin_names_from_cookie_keys( self.request.cookies.keys() )
        self.response.out.write(template.render('templates/main.html', {'oldbins': oldbins}))

    def post(self):
        bin = Bin()
        if bool( self.request.get( 'privatebin' ) ):
            bin.privatebin = make_cookie_vague( bin )
        bin.escapehtml = bool( self.request.get( 'escapehtml' ) )
        bin.put()
        emit_cookie( self, bin )
        self.redirect('/%s' % bin.name)


class BinDeleteHandler(webapp.RequestHandler):
    def post(self):
        name = self.request.path.split('/')[-1]
        if is_valid_postbin_name( name ):
            bin = Bin.all().filter( 'name =', name ).get() # FIX: is this expensive?
            if bin and check_postbin_access( self, bin ):
                if bin.post_set:
                    [p.delete() for p in bin.post_set]
                bin.delete()
        self.redirect( '/' )


class PostDeleteHandler(webapp.RequestHandler):
    def post(self):
        binname = self.request.path.split('/')[-2]
        postname = self.request.path.split('/')[-1]
        deleteall = postname == 'all'
        if deleteall or is_valid_postbin_name( binname ):
            bin = Bin.all().filter( 'name =', binname ).get() # FIX: is this expensive?
            if bin and bin.post_set and check_postbin_access( self, bin ):
                theremustbeabetterway = True
                offset = 0
                while theremustbeabetterway:
                    post = bin.post_set.fetch( 1, offset ) # FIX: there must be a better way
                    offset += 1
                    if post:
                        if deleteall:
                            post[0].delete()
                            offset = 0
                        elif post[0].id() == postname:
                            post[0].delete()
                            theremustbeabetterway = False
                    else:
                        theremustbeabetterway = False
            self.redirect( '/%s' % (binname) )
        else:
            self.redirect( '/' )


# utilities

prefixofbinname = 'pb_'

def is_valid_postbin_name( name, badchars = None ):
    if not badchars:
        badchars = re.compile( '\W' ) # \W is anything that is NOT a letter, number, or underscore
    bin = Bin.all().filter( 'name =', name ).get() # FIX: is this expensive?
    return name and bin and not badchars.search( name )

def is_valid_cookie_postbin_name( name, badchars ):
    return name and name.startswith( prefixofbinname ) and is_valid_postbin_name( name[len( prefixofbinname ):], badchars )

def extract_postbin_names_from_cookie_keys( keys ):
    badchars = re.compile( '\W' ) # \W is anything that is NOT a letter, number, or underscore
    return [s[len( prefixofbinname ):] for s in keys if is_valid_cookie_postbin_name( s, badchars )] # postbin names

def make_cookie_vague( bin ):
    vague = md5.new()
    vague.update( ''.join( [''.join( [c * 56 for c in os.urandom( 42 )] ), 'Webhooks - so simple you\'ll think it\'s stupid'] ) ) # FIX: needs cheaper vagueness
    return '%s_%s' % (bin.name, vague.hexdigest())

def emit_cookie( handler, bin ):
    handler.response.headers.add_header( 'Set-Cookie', '%s%s=%s' % (prefixofbinname, bin.name, bin.privatebin) )
    handler.response.headers.add_header( 'Cache-Control', 'no-cache' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732
    handler.response.headers.add_header( 'Expires', 'Thu, 01 Jan 1970 00:00:00 GMT' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732

def check_postbin_access( handler, bin ):
    retval = True
    if bin.privatebin:
        cookiekey = '%s%s' % (prefixofbinname, bin.name)
        if cookiekey not in handler.request.cookies or bin.privatebin != handler.request.cookies[cookiekey]:
            retval = False
    return retval


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/delete/.*', BinDeleteHandler),('/', MainHandler)], debug=True))
