import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from models import Bin

import md5
import os

class MainHandler(webapp.RequestHandler):
    def get(self):
        oldbins = []
        for k in self.request.cookies.keys():
            if k.find( 'pb_' ) == 0:
                oldbins.append( k[3:] )
        if oldbins:
            self.response.out.write(template.render('templates/main.html', {'oldbins': oldbins}))
        else:
            self.response.out.write(template.render('templates/main.html', {}))

    def post(self):
        bin = Bin()
        bin.privatebin = self.make_secret_maybe()
        bin.escapehtml = bool( self.request.get( 'escapehtml' ) )
        self.response.headers.add_header( 'Set-Cookie', 'pb_' + bin.name + '=' + bin.privatebin )
        bin.put()
        self.redirect('/%s' % bin.name)
    
    def make_secret_maybe( self ):
        retval = ''
        if bool( self.request.get( 'privatebin' ) ):
            secret = md5.new()
            secret.update( 'postbin ' + os.urandom( 42 ) )
            secret.update( secret.hexdigest() )
            secret.update( 'postbin ' + os.urandom( 42 ) )
            retval = secret.hexdigest()
        return retval


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/', MainHandler)], debug=True))
