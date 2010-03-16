#!/usr/bin/python
# -*- coding: utf-8 -*-

from tumblr import Api
import sys, os, time, sqlite3, urllib, re, hashlib
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
	def __init__(self, name, save='./photos', db='./tumblr_photo_down.db'):
		self.name = name
		self.save = save
		self.db   = db
		self.api = Api(name + '.tumblr.com')
		self.pp = pprint.PrettyPrinter(indent=4)
		self._count = 0
		self.posts = None
		self.conn = None
		self._init_db();
		#self.pp.pprint(self.api);
		if os.path.isdir(save) is False:
			os.mkdir(save)

	def count(self):
		if self._count == 0:
			api_url = 'http://' + self.name + '.tumblr.com/api/read/json'
			ret = ''
			try:
				ret = urllib.urlopen(api_url).read()
			except urllib.HTTPError, e:
				raise TumblrPhotoDownError('%s: %s\n' % (e, api_url))
			except urllib.URLError, e:
				raise TumblrPhotoDownError('%s: %s\n' % (e, api_url))
			except:
				raise TumblrPhotoDownError('Unexpected error: %s\n' % (sys.exc_info()[1]))

			m = re.match("^.*?({.*}).*$", ret, re.DOTALL | re.MULTILINE )
			results = simplejson.loads(m.group(1))
			self._count = results['posts-total']

		return self._count;

	def read(self):
		if self.posts == None:
			self.posts = self.api.read()
		return self.posts

	def _init_db(self):
		self.conn = sqlite3.connect(self.db, isolation_level=None)
		try:
			c = self.conn.execute(u'select * from photos')
		except:
			create_sql="""create table photos(
			id INTEGER PRIMARY KEY,
			tumblr_id INTEGER NOT NULL,
			tumblr_photo_link_url TEXT,
			tumblr_image_hash TEXT NOT NULL
			)"""
			self.conn.execute(create_sql)

	def _is_exists_byId(self, tumblr_id):
		return False;

	def _is_exists_byUrl(self, tumblr_photo_link_url):
		if tumblr_photo_link_url is None:
			return False

		c = self.conn.cursor()
		c.execute('select id from photos where tumblr_photo_link_url = ?', (tumblr_photo_link_url,))
		if c.fetchone() is not None:
			return False

		return True;

	def _is_exists_byHash(self, tumblr_image_hash):
		return False;

	def down_all(self):
		posts = self.read();
		for post in posts:
			if post['type'] == 'photo':
				self._down(post);

	def _down(self, post):
		self.pp.pprint(post)
		if      self._is_exists_byId(post['id']) != True and self._is_exists_byUrl(post.get('photo-link-url')) :
			print post['photo-url-1280']
			print os.path.basename(post['photo-url-1280'])
			savepath = self.save + '/' + os.path.basename(post['photo-url-1280'])
			if os.path.basename(post['photo-url-1280']).find('.') == -1:
				_tmp = os.path.basename(post['photo-url-75'])
				savepath += '.' + _tmp.split('.')[1]
			urllib.urlretrieve(post['photo-url-1280'], savepath)
			time.sleep(3)


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: tumblr_photo_down.py TARGET_ID"
		quit()

	tpd = TumblrPhotoDown(sys.argv[1])
	print "target [%s] donwload start" % sys.argv[1]
	print "\ttotal [%s]" % tpd.count()
	tpd.down_all()

