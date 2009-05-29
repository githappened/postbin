import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from models import Bin

import md5
import os

class MainHandler(webapp.RequestHandler):
    def get(self):
        oldbins = [s[3:] for s in self.request.cookies.keys() if s[:3] == 'pb_']
        if oldbins:
            self.response.out.write(template.render('templates/main.html', {'oldbins': oldbins}))
        else:
            self.response.out.write(template.render('templates/main.html', {}))

    def post(self):
        bin = Bin()
        bin.privatebin = self.make_secret_maybe( bin )
        bin.escapehtml = bool( self.request.get( 'escapehtml' ) )
        self.response.headers.add_header( 'Set-Cookie', 'pb_' + bin.name + '=' + bin.privatebin )
        self.response.headers.add_header( 'Cache-Control', 'no-cache' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732
        self.response.headers.add_header( 'Expires', 'Fri, 01 Jan 1990 00:00:00 GMT' ) # FIX: attempt to avoid cache bug? http://code.google.com/p/googleappengine/issues/detail?id=732
        bin.put()
        self.redirect('/%s' % bin.name)
    
    def make_secret_maybe( self, bin ):
        retval = ''
        if bool( self.request.get( 'privatebin' ) ):
            retval += bin.name
            secret = md5.new()
            secret.update( 'postbin ' + os.urandom( 42 ) )
            secret.update( secret.hexdigest() )
            retval += '_' + secret.hexdigest()
            secret.update( 'postbin ' + os.urandom( 56 ) )
            secret.update( secret.hexdigest() )
            retval += '_' + secret.hexdigest()
        return retval


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/', MainHandler)], debug=True))
