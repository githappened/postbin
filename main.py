import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from models import Bin

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
        bin.privatebin = bool( self.request.get( 'privatebin' ) )
        bin.escapehtml = bool( self.request.get( 'escapehtml' ) )
        self.response.headers.add_header( 'Set-Cookie', 'pb_' + bin.name + '=y' )
        bin.put()
        self.redirect('/%s' % bin.name)

if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/', MainHandler)], debug=True))
