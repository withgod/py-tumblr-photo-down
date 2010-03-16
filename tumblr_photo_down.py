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
		self._coursor = 1
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
			print sys.exc_info()[1]
			print "not found phots table. creating"
			create_sql="""create table photos(
			id INTEGER PRIMARY KEY,
			tumblr_id INTEGER NOT NULL,
			tumblr_photo_link_url TEXT,
			tumblr_image_hash TEXT NOT NULL
			)"""
			self.conn.execute(create_sql)

	def _is_exists_byId(self, tumblr_id):
		c = self.conn.cursor()
		c.execute('select id from photos where tumblr_id = ?', (tumblr_id,))
		if c.fetchone() is None:
			return False

		return True

	def _is_exists_byUrl(self, tumblr_photo_link_url):
		if tumblr_photo_link_url is None:
			return False

		c = self.conn.cursor()
		c.execute('select id from photos where tumblr_photo_link_url = ?', (tumblr_photo_link_url,))
		if c.fetchone() is None:
			return False

		return True

	def _is_exists_byHash(self, tumblr_image_hash):
		c = self.conn.cursor()
		c.execute('select id from photos where tumblr_image_hash= ?', (tumblr_image_hash,))
		if c.fetchone() is None:
			return False

		return True

	def down_all(self):
		posts = self.read();
		for post in posts:
			self._coursor += 1
			if post['type'] == 'photo':
				self._down(post);

	def _down(self, post):
		print "downloading [%s/%s][%s]" % (self._coursor, self._count, post.get('photo-url-1280'))
		if self._is_exists_byId(post['id']) == True:
			print "\tduplicate by id [%s]" % post['id']
			return False

		if self._is_exists_byUrl(post.get('photo-link-url')) == True:
			print "\tduplicate by photo-link-url [%s]" % post.get('photo-link-url')
			return False

		#print post['photo-url-1280']
		#print os.path.basename(post['photo-url-1280'])
		savepath = self.save + '/' + os.path.basename(post['photo-url-1280'])
		if os.path.basename(post['photo-url-1280']).find('.') == -1:
			_tmp = os.path.basename(post['photo-url-75'])
			savepath += '.' + _tmp.split('.')[1]

		if os.path.basename(post['photo-url-75']).split('.')[1] != 'jpg':
			print "\tnot jpg file[%s]" % savepath
			return False

		urllib.urlretrieve(post['photo-url-1280'], savepath)

		m = hashlib.md5()
		for f in open(savepath, 'rb'):
			m.update(f)
		hash = m.hexdigest()

		if self._is_exists_byHash(hash) == True:
			print "\tduplicate by hash [%s]" % hash
			os.remove(savepath)
			return False

		self.conn.execute('insert into photos(tumblr_id, tumblr_photo_link_url, tumblr_image_hash) values (?, ?, ?)',
				(post['id'], post.get('photo-link-url'), hash))

		time.sleep(1)


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: tumblr_photo_down.py TARGET_ID"
		quit()

	tpd = TumblrPhotoDown(sys.argv[1])
	print "target [%s] donwload start" % sys.argv[1]
	print "\ttotal [%s]" % tpd.count()
	tpd.down_all()

