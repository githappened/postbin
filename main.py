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
            bin.privatebin = make_cookie_secret( bin )
        bin.escapehtml = bool( self.request.get( 'escapehtml' ) )
        bin.put()
        emit_cookie( self, bin )
        self.redirect('/%s' % bin.name)


class BinDeleteHandler(webapp.RequestHandler):
    def post(self):
        name = self.request.path.split('/')[-1]
        if is_valid_postbin_name( name ):
            bin = Bin.all().filter( 'name =', name ).get() # FIX: is this expensive?
            if( bin ):
                if bin.post_set:
                    [p.delete() for p in bin.post_set]
                bin.delete()
        self.redirect( '/' )


class PostDeleteHandler(webapp.RequestHandler):
    def post(self):
        binname = self.request.path.split('/')[-2]
        postname = self.request.path.split('/')[-1]
        if is_valid_postbin_name( binname ):
            bin = Bin.all().filter( 'name =', binname ).get() # FIX: is this expensive?
            if bin and bin.post_set:
                theremustbeabetterway = True
                offset = 0
                while theremustbeabetterway:
                    post = bin.post_set.fetch( 1, offset ) # FIX: there must be a better way
                    offset += 1
                    if post:
                        if post[0].id() == postname:
                            post[0].delete()
                            theremustbeabetterway = False
                    else:
                        theremustbeabetterway = False
            self.redirect( '/%s' % (binname) )
        else:
            self.redirect( '/' )


# utilities

def is_valid_postbin_name( name, badchars = None ):
    if not badchars:
        badchars = re.compile( '\W' ) # \W is anything that is NOT a letter, number, or underscore
    bin = Bin.all().filter( 'name =', name ).get() # FIX: is this expensive?
    return name and bin and not badchars.search( name )

def is_valid_cookie_postbin_name( name, badchars ):
    return name and name[:3] == 'pb_' and is_valid_postbin_name( name[3:], badchars )

def extract_postbin_names_from_cookie_keys( keys ):
    badchars = re.compile( '\W' ) # \W is anything that is NOT a letter, number, or underscore
    return [s[3:] for s in keys if is_valid_cookie_postbin_name( s, badchars )] # postbin names, remove pb_ prefix

def make_cookie_secret( bin ):
    secret = md5.new()
    secret.update( "Webhooks - so simple you'll think it's stupid" + os.urandom( 42 ) )
    return '%s_%s' % (bin.name, secret.hexdigest())

def emit_cookie( handler, bin ):
    handler.response.headers.add_header( 'Set-Cookie', 'pb_%s=%s' % (bin.name, bin.privatebin) )
    handler.response.headers.add_header( 'Cache-Control', 'no-cache' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732
    handler.response.headers.add_header( 'Expires', 'Thu, 01 Jan 1970 00:00:00 GMT' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732

def check_postbin_secret( handler, bin ):
    retval = True
    if bin.privatebin:
        cookiekey = 'pb_%s' % (bin.name)
        if cookiekey not in handler.request.cookies or bin.privatebin != handler.request.cookies[cookiekey]:
            retval = False
    return retval


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/delete/.*', BinDeleteHandler),('/', MainHandler)], debug=True))
