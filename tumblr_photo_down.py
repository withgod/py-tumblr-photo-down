#!/usr/bin/python
# -*- coding: utf-8 -*-

from tumblr import Api
import sys, sqlite3, urllib2, re
import pprint

try:
    import simplejson
except ImportError:
    from django.utils import simplejson

class TumblrPhotoDownError(Exception):
	''' General TumblrPohotoDown error ''' 
	def __init__(self, msg):
		self.msg = msg 

	def __str__(self):
		return self.msg 

class TumblrPhotoDown:
	def __init__(self, name, save='./', db='./'):
		self.name = name
		self.save = save
		self.db   = db
		self.api = Api(name + '.tumblr.com')
		self.pp = pprint.PrettyPrinter(indent=4)
		self._count = 0
		#self.pp.pprint(self.api);

	def count(self):
		if (self._count == 0):
			api_url = 'http://' + self.name + '.tumblr.com/api/read/json'
			ret = ''
			try:
				ret = urllib2.urlopen(api_url).read()
			except urllib2.HTTPError, e:
				raise TumblrPhotoDownError('%s: %s\n' % (e, api_url))
			except urllib2.URLError, e:
				raise TumblrPhotoDownError('%s: %s\n' % (e, api_url))
			except:
				raise TumblrPhotoDownError('Unexpected error: %s\n' % (sys.exc_info()[1]))

			m = re.match("^.*?({.*}).*$", ret, re.DOTALL | re.MULTILINE )
			results = simplejson.loads(m.group(1))
			self._count = results['posts-total']

		return self._count;

	def down(self):
		print "do down"
		posts = self.api.read()
		for post in posts:
			print "post type [%s]\n" % post['type']
			self.pp.pprint(post)


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: tumblr_photo_down.py TARGET_ID"
		quit()

	tpd = TumblrPhotoDown(sys.argv[1])
	print "total [%s]" % tpd.count()
	#tpd.down()
