import wsgiref.handlers
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from models import Bin, Post
import urllib

import main

class BinHandler(webapp.RequestHandler):
    def get(self):
        if self.request.path[-1] == '/':
            self.redirect(self.request.path[:-1])
        bin = self._get_bin()
        if bin:
            if not main.check_postbin_access( self, bin ):
                self.redirect( '/' )
            posts = bin.post_set.order('-created').fetch(50)
            request = self.request
            self.response.out.write(template.render('templates/bin.html', {'bin':bin, 'posts':posts, 'request':request}))
        else:
            self.redirect( '/' )

    def post(self):
        bin = self._get_bin()
        if bin:
            post = Post(bin=bin, remote_addr=self.request.remote_addr)
            post.headers        = dict(self.request.headers)
            post.body           = self.request.body
            post.query_string   = self.request.query_string
            post.form_data      = dict(self.request.POST)
            post.put()
            if 'http://' in self.request.query_string:
                urlfetch.fetch(url=self.request.query_string.replace('http://', 'http://hookah.webhooks.org/'), 
                                payload=urllib.urlencode(dict(self.request.POST)), method='POST')
            self.redirect('/%s' % bin.name)
        else:
            self.redirect( '/' )
        
    def _get_bin(self):
        name = self.request.path.replace('/', '')
        bin = Bin.all().filter('name =', name).get()
        if bin:
            return bin
        else:
            self.redirect('/')


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([('/delete/.*/.*', main.PostDeleteHandler),('/.*', BinHandler)], debug=True))
