"""
These tests will pass when you run "manage.py test".
"""

from django.test import TestCase
from django.db.models.fields import FieldDoesNotExist
import unittest
from django.db import models
from django.contrib.auth.models import User
from models import Picture, Page, Album, Section, Profile
from operator import attrgetter
from django.core.exceptions import ValidationError
from django.test.client import Client
from albumapp.views import search_flickr, add_picture_url_to_database
from albumapp.views import FLICKR_SEARCH_RESULT_COUNT
from django.test.client import RequestFactory
import re

def _test_no_template_used(test_case, response, except_these = None):
    # each time you add/remove/change a new template, update the list here
    all_templates = ['albums/index.html', 'albums/edit.html', 'albums/new.html', 
                    'pages/index.html', 'pages/show.html', 'pages/templates.html',
                    'pictures/index.html', 'shared/footer.html', 'shared/header.html', 
                    '400.html', '404.html', 'base.html']

    for template in except_these:
        #print template
        all_templates.remove(template)
        test_case.assertTemplateUsed(response, template, "error %s not used" % template)
         
    for template in all_templates:
        test_case.assertTemplateNotUsed(response, template, "error %s is used" % template)
            
class AlbumAppViewTests(TestCase):
    
    fixtures = ['unit_test_empty.xml']
    
    def setUp(self):
        # Initialize a Django test client
        self.client = Client()
        # why do we delete all objects? Production db objects ends up
        # in our test db: 
        # https://docs.djangoproject.com/en/dev/topics/testing/overview/#the-test-database
        # tells more about it but i coudn't understand the problem
        # a similar issue has been reported as Django bug too
        # https://groups.google.com/forum/?fromgroups=#!topic/django-non-relational/vBBhyZcidL4
        Album.objects.all().delete()
        Page.objects.all().delete()
        Section.objects.all().delete()
        Picture.objects.all().delete()
        user = User.objects.create_user("username", "email@testi.fi", "123456")
        user.save()
        self.profile = Profile.create(user)
        self.album = Album.create('Album for delete_album tests', 'page_text', self.profile)
        self.picture = Picture.create('http://farm9.staticflickr.com/8308/7842351432_76cafc4191.jpg')
        # self._show_db_content('setup')
        self.except_these = ['albums/index.html', 'albums/new.html', 'shared/footer.html', 'shared/header.html', 'base.html']
        self.except_these_2 = ['pages/index.html', "pages/templates.html", "pictures/index.html", 'shared/footer.html', 'shared/header.html', 'base.html']
        self.too_long_page_title = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss'
        self.too_long_section_caption = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'   
        user = self.client.login(username='username', password='123456')         

    # this cookie check function can be duplicated for other view functions
    # it is not duplicated for now, as we don't know the future use of cookie returns from views
    def _test_this_field_cannot_be_blank_cookie(self, response):
        messages_cookie = response.cookies.get('messages')
        re1='.*?'    # Non-greedy match on filler
        re2='(\'This field cannot be blank\\.\')'    # Single Quote String 1
            
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(messages_cookie.__str__())
        self.assertTrue(len(m.group(1)), '_test_this_field_cannot_be_blank_cookie failed') 
    
    def _is_album_in_db(self, album_title, page_text, expected_result):
        result = False
        try:
            album = Album.objects.get(title = album_title)
            page = Page.objects.get(text = page_text)
            result = album.is_page_present(page)
        except Album.DoesNotExist, Page.DoesNotExist:
            result = False
        self.assertEqual(result, expected_result, '_is_album_in_db failed observed %s and expected %s' % (result, expected_result))
    
    def _form_data(self, title = None, page_text = None, album_id = None, page_id = None, picture_id = None, section_id = None, section_caption = None):
        data = {}
        if title != None:
            data['title'] = title
            data['new_album_title'] = title
        if page_text != None:
            data['page_text'] = page_text
            data['new_page_text'] = page_text
        if album_id != None:
            data['album_id'] = album_id
        if page_id != None:
            data['page_id'] = page_id
            data['page_pk'] = page_id
        if picture_id != None:
            data['picture_id'] = picture_id
            data['picture_pk'] = picture_id
        if section_id != None:
            data['section_id'] = section_id
            data['section_pk'] = section_id
        if section_caption != None:
            data['section_caption'] = section_caption
        return data
    
    def _test_create_album_failures_with_post(self, _is_album_created = False, _title = None, _page_text = None):
        old_count = Album.objects.all().count()
        data = self._form_data(_title, _page_text)
        # make a (bad request based on data)  & do not follow redirect
        response = self.client.post('/albums/create_album/', data, follow=False)
        self.assertEquals(response.status_code, 302, "testing make a bad request with no params returns %s" % response.status_code)     
        if _title is None or not len(_title):
            self._test_this_field_cannot_be_blank_cookie(response)
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, '_test_create_album_failures_with_post failed oldcount %s and newcount %s' % (old_count, new_count))

        # make a (bad request based on data)  & do  follow redirect
        response = self.client.post('/albums/create_album/', data, follow=True)
        self.assertEquals(response.status_code, 200, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = self.except_these)
        self.assertRedirects(response, 'http://testserver/albums/index/', 302, host = 'testserver')
        self._is_album_in_db(album_title = _title, page_text = _page_text, expected_result = _is_album_created)
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, '_test_create_album_failures_with_post failed oldcount %s and newcount %s' % (old_count, new_count))

    def _test_create_album_failures_with_get(self, _is_album_created = False, _title = None, _page_text = None):
        old_count = Album.objects.all().count()
        # make a bad request (coz its GET) based on data  & do not follow redirect
        data = self._form_data(_title, _page_text)
        response = self.client.get('/albums/create_album/', data, follow=False)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)     
        self._is_album_in_db(album_title = _title, page_text = _page_text, expected_result = _is_album_created)
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, '_test_create_album_failures_with_get failed oldcount %s and newcount %s' % (old_count, new_count))
        
        # make a bad request (coz its GET)  & do  follow redirect
        response = self.client.get('/albums/create_album/', data, follow=True)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, '_test_create_album_failures_with_get failed oldcount %s and newcount %s' % (old_count, new_count))
 
    def _show_db_content(self, test_name):
        print test_name
        print 'Album.objects.all()', Album.objects.all()
        print 'Page.objects.all()', Page.objects.all()
        print ''

    def test_create_album_none_title_none_page_text(self):
        self._test_create_album_failures_with_post()
        self._test_create_album_failures_with_get()
        # self._show_db_content('test_create_album_none_title_none_page_text')

    def test_create_album_none_title_with_page_text(self):
        self._test_create_album_failures_with_post(_is_album_created = False, _page_text='non empty')
        self._test_create_album_failures_with_get(_is_album_created = False, _page_text='non empty')
        # self._show_db_content('test_create_album_none_title_none_page_text')
           
    def test_create_album_empty_title_empty_page_text(self):
        self._test_create_album_failures_with_post(_is_album_created = False, _title = '', _page_text='')
        self._test_create_album_failures_with_get(_is_album_created = False, _title = '', _page_text='')
        # self._show_db_content('test_create_album_empty_title_empty_page_text')
    
    def test_create_album_empty_title_with_page_text(self):   
        self._test_create_album_failures_with_post(_is_album_created = False, _title = '', _page_text='non empty')
        self._test_create_album_failures_with_get(_is_album_created = False, _title = '', _page_text='non empty')
        # self._show_db_content('test_create_album_empty_title_with_page_text')

    def _test_create_album_success_with_post(self, _title, _page_text, _is_album_created = True):
        # make a valid request where album is supposed to be created
        data = {'title': _title, 'page_text': _page_text}
        response = self.client.post('/albums/create_album/', data, follow=True)
        self.assertEquals(response.status_code, 200, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = self.except_these)
        self.assertRedirects(response, 'http://testserver/albums/index/', 302, host = 'testserver')
        self._is_album_in_db(album_title = _title, page_text = _page_text, expected_result = _is_album_created)

    def test_create_album_with_title_with_page_text(self):        
        self._test_create_album_success_with_post(_is_album_created = True, _title = 'non empty', _page_text='non empty')
        # self._show_db_content('test_create_album_with_title_with_page_text')
  
    def test_create_album_with_title_empty_page_text(self):       
        self._test_create_album_success_with_post(_is_album_created = True, _title = 'non empty 2', _page_text='')
        # self._show_db_content('test_create_album_with_title_empty_page_text')

    def _is_album_with_id_in_db(self, _album_id, expected_result):
        result = True
        try:
            Album.objects.get(id = _album_id)
        except Album.DoesNotExist, Page.DoesNotExist:
            result = False
        self.assertEqual(result, expected_result, '_is_album_in_db failed observed %s and expected %s' % (result, expected_result))

    def _test_delete_album_with_post(self, _album_id = None):
        data = self._form_data(album_id = _album_id)
        # make a (bad request based on data) with _album_id & do not follow redirect
        response = self.client.post('/albums/delete_album/', data, follow=False)
        self.assertEquals(response.status_code, 302, "testing make a bad request with no params returns %s" % response.status_code)

        # make a (bad request based on data) with _album_id & follow redirect
        response = self.client.post('/albums/delete_album/', data, follow=True)
        self.assertEquals(response.status_code, 200, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = self.except_these)
        self.assertRedirects(response, 'http://testserver/albums/index/', 302, host = 'testserver')

    def _test_delete_album_failures_with_get(self, _album_id = None):
        data = self._form_data(album_id = _album_id)
        # make a bad request (coz its GET) & do not follow redirect
        response = self.client.get('/albums/delete_album/', data, follow=False)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)     

        # make a bad request (coz its GET) & follow redirect
        response = self.client.get('/albums/delete_album/', data, follow=True)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])

    def test_delete_album_failure_with_none_album_id(self):
        old_count = Album.objects.all().count()
        self._test_delete_album_with_post()
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_none_album_id failed oldcount %s and newcount %s' % (old_count, new_count))
        
        old_count = Album.objects.all().count()
        self._test_delete_album_failures_with_get()
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_none_album_id failed oldcount %s and newcount %s' % (old_count, new_count))
 
    def test_delete_album_failure_with_empty_string_album_id(self):
        old_count = Album.objects.all().count()
        self._test_delete_album_with_post(_album_id = '')
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_empty_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count))
        
        old_count = Album.objects.all().count()
        self._test_delete_album_failures_with_get(_album_id = '')
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_empty_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count))   
 
    def test_delete_album_failure_with_bad_string_album_id(self):
        old_count = Album.objects.all().count()
        self._test_delete_album_with_post(_album_id = 'xx')
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = Album.objects.all().count()
        self._test_delete_album_failures_with_get(_album_id = 'xx')
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count))

    def test_delete_album_success(self):
        old_count = Album.objects.all().count()
        self._test_delete_album_with_post(_album_id = self.album.id)
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count+1, 'test_delete_album_success failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_delete_album_failure_with_get(self):
        old_count = Album.objects.all().count()
        self._test_delete_album_failures_with_get(_album_id = self.album.id)
        new_count = Album.objects.all().count()
        self.assertEqual(old_count, new_count, 'test_delete_album_failure_with_get failed oldcount %s and newcount %s' % (old_count, new_count)) 
     
    def _test_add_page_to_album_with_post(self, _album_id = None, _title = None):
        is_valid_album_id = isinstance(_album_id, (int, long)) and len(Album.objects.filter(id = _album_id)) == 1
        # make a (bad request acc.to data) with _album_id & do not follow redirect
        data = self._form_data(album_id = _album_id, title = _title)
        
        response = self.client.post('/albums/add_page_to_album/', data, follow=False)
        if not is_valid_album_id:
            self.assertEquals(response.status_code, 404, "testing make a bad request with no params returns %s" % response.status_code)
        
        # make a (bad request acc.to data) with _album_id & do  follow redirect
        response = self.client.post('/albums/add_page_to_album/', data, follow=True)
        if not is_valid_album_id:
            self.assertEquals(response.status_code, 404, "testing make a bad request with no params returns %s" % response.status_code)
            _test_no_template_used(self,response, except_these = ["404.html"])
        else:
            expected_redirect_url = '/albums/'+ str(_album_id) +'/pages/index/'
            self.assertEquals(response.status_code, 200, "testing make a bad request with no params returns %s" % response.status_code)
            _test_no_template_used(self,response, except_these = self.except_these_2)
        
    def _test_add_page_to_album_failures_with_get(self, _album_id = None, _title = None):
        # make a bad request (coz its get) & do not follow redirect
        data = self._form_data(album_id = _album_id, title = _title)
        response = self.client.get('/albums/add_page_to_album/', data, follow=False)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)     

        # make a bad request (coz its get) & do follow redirect
        response = self.client.get('/albums/add_page_to_album/', data, follow=True)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])
        
    def test_add_page_to_album_failure_with_none_album_id_none_page_title(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post()
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_none_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get()
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_none_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_failure_with_none_album_id_empty_page_title(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post(_title = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_none_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get(_title = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_none_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_failure_with_empty_album_id_none_page_title(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post(_album_id = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_empty_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get(_album_id = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_empty_album_id_none_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_failure_with_empty_album_id_empty_page_title(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post(_album_id = '', _title = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_empty_album_id_empty_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get(_album_id = '', _title = '')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_empty_album_id_empty_page_title failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_failure_with_bad_string_album_id(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post(_album_id = 'xx', _title = 'page title')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get(_album_id = 'xx', _title = 'page title')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_failure_with_too_long_page_title(self):
        old_count = self.album.pages.count()
        self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = self.too_long_page_title)
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

        old_count = self.album.pages.count()
        self._test_add_page_to_album_failures_with_get(_album_id = self.album.id, _title = self.too_long_page_title)
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_add_page_to_album_failure_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_add_page_to_album_save_failure(self):
        # try to fail the album.add_page part and see if database stays intact (i.e. fully commit or rollback)
        self.album.title = 'raise exception' # this will cause exception at Album.add_page in self.save()
        super(Album, self.album).save()  # by-pass our over-riding function, so we don't go through custom validation
        
        old_album_pages_count = self.album.pages.count()
        old_pages_count = Page.objects.all().count()
        self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        new_album_pages_count = Album.objects.get(id = self.album.id).pages.count()
        new_pages_count = Page.objects.all().count()        
        self.assertEqual(old_album_pages_count, new_album_pages_count, 'test_add_page_to_album_save_failure failed old_album_pages_count %s and new_album_pages_count %s' % (old_album_pages_count, new_album_pages_count)) 
        self.assertEqual(old_pages_count, new_pages_count, 'test_add_page_to_album_save_failure failed old_pages_count %s and new_pages_count %s' % (old_pages_count, new_pages_count)) 

        # do the same jazz with GET method, we should get 400
        old_album_pages_count = self.album.pages.count()
        old_pages_count = Page.objects.all().count()
        self._test_add_page_to_album_failures_with_get(_album_id = self.album.id, _title = 'page text')
        new_album_pages_count = Album.objects.get(id = self.album.id).pages.count()
        new_pages_count = Page.objects.all().count()        
        self.assertEqual(old_album_pages_count, new_album_pages_count, 'test_add_page_to_album_save_failure failed old_album_pages_count %s and new_album_pages_count %s' % (old_album_pages_count, new_album_pages_count)) 
        self.assertEqual(old_pages_count, new_pages_count, 'test_add_page_to_album_save_failure failed old_pages_count %s and new_pages_count %s' % (old_pages_count, new_pages_count)) 

    #def test_add_page_to_album_success(self):
    #    # try with creating a blank page 
    #    old_count = self.album.pages.count()
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    new_count = Album.objects.get(id = self.album.id).pages.count()
    #    # makes 2 valid posts, so 2 pages added
    #    self.assertEqual(old_count + 2, new_count, 'test_add_page_to_album_success failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def _test_remove_page_from_album_with_post(self, _album_id = None, _page_id = None):

        is_valid_album_id = isinstance(_album_id, (int, long)) and len(Album.objects.filter(id = _album_id)) == 1
        is_valid_page_id = isinstance(_page_id, (int, long)) and len(Page.objects.filter(id = _page_id)) == 1
        is_page_albums_last_page = is_valid_album_id and is_valid_page_id and (Album.objects.get(id = _album_id).pages.filter(id = _page_id).count() == 1) and (Album.objects.get(id = _album_id).pages.count() == 1)
        old_album_pages_count = self.album.pages.count()
        #print 'album id', _album_id, is_valid_album_id
        #print 'page id', _page_id, is_valid_page_id
        #print 'is_page_albums_last_page', is_page_albums_last_page
    
        data = self._form_data(album_id = _album_id, page_id = _page_id)
        # make a (bad request) with & follow redirect
        response = self.client.post('/albums/remove_page_from_album/', data, follow=True)
        #print 'after post:', Album.objects.get(id = self.album.id).pages.count()
        
        # based on the validity of the request, we use different templates on view side
        # these need to be checked with care
        if (not is_valid_album_id) or (not is_valid_page_id):
            expected_redirect_url = ''
            self.except_these = ['404.html']
            # use the existing self.except_these in setup()
        elif is_valid_album_id and is_valid_page_id:         
            expected_redirect_url = '/albums/'+ str(_album_id) +'/pages/index/'
            self.except_these = ['pages/index.html', 'base.html', 'shared/header.html', 'pages/templates.html', 'pictures/index.html', 'shared/footer.html']
            self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
            new_album_pages_count = self.album.pages.count()
            if is_page_albums_last_page:
                self.assertEqual(old_album_pages_count, new_album_pages_count, 'test_remove_page_failed_oldcount %s and newcount %s' % (old_album_pages_count, new_album_pages_count))
            else:
                self.assertNotEqual(old_album_pages_count, new_album_pages_count, 'test_remove_page_failed_oldcount %s and newcount %s' % (old_album_pages_count, new_album_pages_count))
        #print 'expected_redirect_url', expected_redirect_url
        #print 'self.except_these', self.except_these
        _test_no_template_used(self,response, except_these = self.except_these)
        

    def _test_remove_page_from_album_failures_with_get(self, _album_id = None, _page_id = None):
        # make a bad request with empty 'title' and 'page_text' & do not follow redirect
        data = self._form_data(album_id = _album_id, page_id = _page_id)
        response = self.client.get('/albums/remove_page_from_album/', data, follow=False)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)     

        # make a bad request with empty 'title' and 'page_text' & follow redirect
        response = self.client.get('/albums/remove_page_from_album/', data, follow=True)
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])

    def test_remove_page_from_album_failure_with_none_album_id(self):
        #print 'test_remove_page_from_album_failure_with_none_album_id'
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_with_post()
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_none_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 
        
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_failures_with_get()
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_none_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 
 
    def test_remove_page_from_album_failure_with_empty_string_album_id(self):
        #print 'test_remove_page_from_album_failure_with_empty_string_album_id '      
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_with_post(_album_id='')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_empty_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 
        
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_failures_with_get(_album_id='')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_empty_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_remove_page_from_album_failure_with_bad_string_album_id(self):
        #print 'test_remove_page_from_album_failure_with_bad_string_album_id'        
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_with_post(_album_id='xx')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 
        
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_failures_with_get(_album_id='xx')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_with_bad_string_album_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

    def test_remove_page_from_album_failure_with_bad_string_page_id(self):
        #print 'test_remove_page_from_album_failure_with_bad_string_page_id'         
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_with_post(_album_id = self.album.id, _page_id='xx')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_bad_string_page_id failed oldcount %s and newcount %s' % (old_count, new_count)) 
        
        old_count = self.album.pages.count()
        self._test_remove_page_from_album_failures_with_get(_album_id = self.album.id, _page_id='xx')
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_bad_string_page_id failed oldcount %s and newcount %s' % (old_count, new_count)) 

    #def test_remove_page_from_album_success(self):
    #    #print 'test_remove_page_from_album_success'       
    #    self.test_add_page_to_album_success()  # add to 2 more pages to our 1 page album
    #    old_count = self.album.pages.count()
    #    i = 1;
    #    for page in self.album.pages.all():
    #        #print page
    #        self._test_remove_page_from_album_with_post(_album_id = self.album.id, _page_id=page.id)
    #        new_count = Album.objects.get(id = self.album.id).pages.count()
    #        self.assertEqual(old_count, new_count+i, 'test_remove_page_from_album_success failed oldcount %s and newcount %s' % (old_count, new_count))
    #        i+=1
    #        if Album.objects.get(id = self.album.id).pages.count() == 1:
    #            break  # the Album is designed to not to delete its last page, for that refer to test_remove_page_from_album_failure_last_page
            
    def test_remove_page_from_album_failure_last_page(self):
        #print 'test_remove_page_from_album_failure_last_page'        
        # at this point our album has only 1 page
        old_count = self.album.pages.count()
        self.assertEqual(old_count, 1, 'test_remove_page_from_album_failure_last_page failed oldcount %s ' % (old_count))
        # get the only page our album has
        page = Page.objects.filter(album__pk = self.album.id)[0]
        self._test_remove_page_from_album_with_post(_album_id = self.album.id, _page_id=page.id)
        new_count = Album.objects.get(id = self.album.id).pages.count()
        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_last_page failed oldcount %s and newcount %s' % (old_count, new_count)) 
 

    #def test_remove_page_from_album_failure_with_get(self):
    #    #print 'test_remove_page_from_album_failure_with_get'       
    #    self.test_add_page_to_album_success()  # add to 2 more pages to our 1 page album     
    #    old_count = self.album.pages.count()
    #    for page in self.album.pages.all():
    #        old_count = self.album.pages.count()
    #        self._test_remove_page_from_album_failures_with_get(_album_id = self.album.id, _page_id=page.id)
    #        new_count = Album.objects.get(id = self.album.id).pages.count()
    #        self.assertEqual(old_count, new_count, 'test_remove_page_from_album_failure_with_get failed oldcount %s and newcount %s' % (old_count, new_count))
            
    def test_change_album_title_with_post_valid(self):
        data = self._form_data(album_id = self.album.id, title = "new_album_title")
        old_title = self.album.title
       
        response = self.client.post('/albums/change_album_title/', data, follow=True)
        new_title = Album.objects.get(id = self.album.id).title
        
        expected_redirect_url = "/albums/index/"
        self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        self.assertNotEqual(old_title, new_title, 'test change album title failed with title old: %s and title new: %s' % (old_title, new_title))
        

    def test_change_album_title_with_post_invalid(self):   
        #CASE 1: empty title
        data = self._form_data(album_id = self.album.id, title = "")
        old_title = self.album.title
        
        response = self.client.post('/albums/change_album_title/', data, follow=True)
        new_title = Album.objects.get(id = self.album.id).title
        
        expected_redirect_url = "/albums/index/"
        self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        self.assertEqual(old_title, new_title, 'test_change_album_title_with_post_invalid failed with title old: %s and title new: %s' % (old_title, new_title))
        
        #CASE 2: too long title
        data = self._form_data(album_id = self.album.id, title = self.too_long_page_title)
        
        response = self.client.post('/albums/change_album_title/', data, follow=True)
        new_title = Album.objects.get(id = self.album.id).title
        
        expected_redirect_url = "/albums/index/"
        self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        self.assertEqual(old_title, new_title, 'test_change_album_title_with_post_invalid failed with title old: %s and title new: %s' % (old_title, new_title))        

        #CASE 2: no album id
        data = self._form_data(title = self.too_long_page_title)
        
        response = self.client.post('/albums/change_album_title/', data, follow=True)
        new_title = Album.objects.get(id = self.album.id).title
        
        self.assertEqual(response.status_code, 404, 'test_change_album_title_with_post_invalid failed with response received: %s and expected: %s' % (response.status_code, 404))
        self.assertEqual(old_title, new_title, 'test_change_album_title_with_post_invalid failed with title old: %s and title new: %s' % (old_title, new_title))   
    
    def test_change_album_title_with_get(self):
        data = self._form_data(album_id = self.album.id, title = "new_album_title")
        response = self.client.get('/albums/change_album_title/', data, follow=True)
        
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])
            
    #def test_change_page_text_post_valid(self):
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    page = Page.objects.filter(album__pk = self.album.id)[0]
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, page_text = "new_page_text")

    #    old_text = page.text

    #    response = self.client.post('/albums/change_page_text/', data, follow=True)
        
    #    new_text = Page.objects.get(id = page.id).text
        
    #    expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
    #    self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
    #    self.assertNotEqual(old_text, new_text, 'test change page text failed with text old: %s and text new: %s' % (old_text, new_text))

    #def test_change_page_text_post_invalid(self):
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    page = Page.objects.filter(album__pk = self.album.id)[0]
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, page_text = self.too_long_page_title)
    #    old_text = page.text
        
    #    response = self.client.post('/albums/change_page_text/', data, follow=True)
        
    #    new_text = page.text
        
    #    expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
    #    self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
    #    self.assertEqual(old_text, new_text, 'test change album title failed with title old: %s and title new: %s' % (old_text, new_text)) 
    
    #def test_change_page_text_get(self):
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    page = Page.objects.filter(album__pk = self.album.id)[0]
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, page_text = "new_page_text")
    #    response = self.client.get('/albums/change_page_text/', data, follow=True)
        
    #    self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
    #    _test_no_template_used(self,response, except_these = ['400.html'])
    
    #def test_create_section_post_valid(self):
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    page = Page.objects.filter(album__pk = self.album.id)[0]
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, picture_id = self.picture.pk, section_caption = "new section")
    #    old_count = Section.objects.all().count()
        
    #    response = self.client.post('/pages/create_section/', data, follow=True)
        
    #    expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
    #    self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
    #    count = Section.objects.all().count()
    #    self.assertEqual(old_count, count - 1, 'test create section post valid failed with old section count: %s and new section count: %s' % (old_count, count))  
    
    #def test_create_section_post_invalid(self):
    #    self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
    #    page = Page.objects.filter(album__pk = self.album.id)[0]
    #    
        #Case 1: No image selected
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, picture_id = None, section_caption = "new section")
    #    old_count = Section.objects.all().count()
        
    #    response = self.client.post('/pages/create_section/', data, follow=True)

    #    expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
    #    self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
    #    count = Section.objects.all().count()
    #    self.assertEqual(old_count, count, 'test create section post valid failed with old section count: %s and new section count: %s' % (old_count, count))
        
        #Case 2: Too long section caption
        
    #    data = self._form_data(album_id = self.album.id, page_id = page.id, picture_id = None, section_caption = self.too_long_section_caption)
        
    #    response = self.client.post('/pages/create_section/', data, follow=True)

    #    expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
    #    self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
    #    count = Section.objects.all().count()
    #    self.assertEqual(old_count, count, 'test create section post valid failed with old section count: %s and new section count: %s' % (old_count, count))
       
    #def test_create_section_get(self):
    #    data = self._form_data(album_id = self.album.id, title = "new_album_title")
    #    response = self.client.get('/albums/change_album_title/', data, follow=True)
        
    #    self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
    #    _test_no_template_used(self,response, except_these = ['400.html'])
    
    #def test_remove_section_post(self):
        #self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        #page = Page.objects.filter(album__pk = self.album.id)[0]
        #section = Section.create(self.picture, page, "This is section")
        #data = self._form_data(album_id = self.album.id, page_id = page.id, section_id = section.pk)
        
        #old_count = Section.objects.all().count()
        
        #response = self.client.post('/pages/remove_section/', data, follow=True)
        
        #expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
        #self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        #count = Section.objects.all().count()
        #self.assertEqual(old_count, count + 1, 'test create section post valid failed with old section count: %s and new section count: %s' % (old_count, count))  
    
    #def test_remove_section_get(self):
        #self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        #page = Page.objects.filter(album__pk = self.album.id)[0]
        #section = Section.create(self.picture, page, "This is section")
        #data = self._form_data(album_id = self.album.id, page_id = page.id, section_id = section.pk)
        #
        #response = self.client.get('/pages/remove_section/', data, follow=True)
        #
        #self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        #_test_no_template_used(self,response, except_these = ['400.html'])
    
    # CHANGE_PICTURE_LINK, are we gonna need this one from the UI?
    
    def change_section_caption_post_valid(self):
        self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        page = Page.objects.filter(album__pk = self.album.id)[0]
        section = Section.create(self.picture, page, "This is section")
        data = self._form_data(album_id = self.album.id, page_id = page.id, section_id = section.pk, new_section_caption = "New caption")
        old_caption = section.caption
        
        response = self.client.get('/pages/change_section_caption/', data, follow=True)
        
        expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
        self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        new_caption = section.caption
        self.assertNotEqual(old_caption, new_caption, 'test change section caption post valid failed with old section caption: %s and new section caption: %s' % (old_caption, new_caption))  
        
    def change_section_caption_post_invalid(self):
        self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        page = Page.objects.filter(album__pk = self.album.id)[0]
        section = Section.create(self.picture, page, "This is section")
        data = self._form_data(album_id = self.album.id, page_id = page.id, section_id = section.pk, new_section_caption = self.too_long_section_caption)
        old_caption = section.caption
        
        response = self.client.get('/pages/change_section_caption/', data, follow=True)
        
        expected_redirect_url = "/albums/"+ str(self.album.id) + "/pages/"+ str(page.id) +"/show/"
        self.assertRedirects(response, expected_redirect_url, 302, host = 'testserver')
        new_caption = section.caption
        self.assertEqual(old_caption, new_caption, 'test change section caption post valid failed with old section caption: %s and new section caption: %s' % (old_caption, new_caption))
    
    def change_section_caption_get(self):
        self._test_add_page_to_album_with_post(_album_id = self.album.id, _title = 'page text')
        page = Page.objects.filter(album__pk = self.album.id)[0]
        section = Section.create(self.picture, page, "This is section")
        data = self._form_data(album_id = self.album.id, page_id = page.id, section_id = section.pk, new_section_caption = "New caption")
        
        response = self.client.get('/pages/change_section_caption/', data, follow=True)
        
        self.assertEquals(response.status_code, 400, "testing make a bad request with no params returns %s" % response.status_code)
        _test_no_template_used(self,response, except_these = ['400.html'])
    
    #def test_add_picture_url_to_database(self):
    #    picture_link = 'http://www.9ori.com/store/media/images/8ab579a656.jpg'
    #    data = {'url' : picture_link, 'album_id' : self.album.id}
    #    self.assertEqual(len(Picture.objects.filter(link=picture_link)), 0, 'Picture link already exists in database.')
    #    self.client.post('/pictures/add_picture_url_to_database/', data, follow=True)
    #    #request = self.factory.post('/pictures/add_picture_url_to_database/', {'url' : picture_link, 'album_id' : 1})
    #    #add_picture_url_to_database(request)
    #    self.assertEqual(len(Picture.objects.filter(link=picture_link)), 1, 'Picture link wasnt added to database.')
'''        
class AlbumAppModelsTests(TestCase, unittest.TestCase):

    #fixtures = ['albums.xml']
    fixtures = ['unit_test_empty.xml']

    def setUp(self):
        user = User.objects.create_user("username", "email@testi.fi", "123456")
        user.save()
        self.profile = Profile.create(user)
        self.picture = Picture.objects.get(link__icontains="solar")
        self.page = Page.objects.get(text__icontains="space")
        self.album_title = 'My photo album'
        self.album = Album.objects.get(title=self.album_title)
        self.new_link = 'http://cdn.sstatic.net/stackoverflow/img/sprites.png'
        self.new_text = 'new text'
        self.bad_link = 'i am a bad url'
        self.expected_query_set = [u'space',]
        self.text = 'space'
        self.section_caption = 'caption'
        self.raise_exception = 'raise exception'
        self.too_long_caption = 'I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption I am too long caption '
     
    def _testfieldtype(self, model, modelname, fieldname, field_type):
        try:
            field = model._meta.get_field(fieldname)
            self.assertTrue(isinstance(field, field_type), "Testing the type of %s field in model %s"%(fieldname, modelname))
        except FieldDoesNotExist:
            self.assertTrue(False, "Testing if field %s exists in model %s"%(fieldname, modelname))
        return field
    
    #def test_unicode_album(self):
    #    albums = Album.objects.all()
    #    for album in albums:
    #        print album

    #def test_unicode_picture(self):
    #    pictures = Picture.objects.all()
    #    for picture in pictures:
    #        print picture

    #def test_unicode_page(self):
    #    pages = Page.objects.all()
    #    for page in pages:
    #        print page

    #def test_unicode_section(self):
    #    self.section = Section(picture = self.picture, page = self.page, caption = self.section_caption)
    #    self.section.save()
    #   print self.section
            
    #Test field types and attributes of Picture, Page and Album classes
    #def test_field_types(self):
    #    self._testfieldtype(Picture, 'Picture', 'link', models.URLField)
    #    self._testfieldtype(Section, 'Section', 'caption', models.TextField)
    #    self._testfieldtype(Page, 'Page', 'text', models.TextField)
    #    self._testfieldtype(Page, 'Page', 'pictures', models.ManyToManyField)
    #    self._testfieldtype(Album, 'Album', 'title', models.CharField)
    #    self._testfieldtype(Album, 'Album', 'pages', models.ManyToManyField)
    
    #def test_field_values_in_db(self):
    #    self.assertEqual(self.picture.link, 'http://www.nasa.gov/images/content/717275main_solar_dance_full_full.jpg')
    #    self.assertEqual(self.page.text, 'space')
    #    self.assertEqual(self.album.title, 'My photo album')
        
    #Tests for picture class
    def test_picture_create_picture(self):
        old_count = Picture.objects.all().count()  
        new_picture = Picture.create(self.new_link)
        verify_new_picture = Picture.objects.all().get(link=self.new_link)
        
        # To compare two model instances, just use the standard Python comparison operator, 
        # the double equals sign: ==. Behind the scenes, that compares the primary key values 
        # of two models
        self.assertTrue(new_picture == verify_new_picture, 'new picture creation failed')
        
        new_count = Picture.objects.all().count()
        self.assertEqual(old_count + 1, new_count, "picture object count mismatch")

    def test_picture_create_same_picture_many_times(self):
        old_count = Picture.objects.all().count()
        new_picture = Picture.create(self.new_link)
        new_count = Picture.objects.all().count()
        self.assertEqual(old_count + 1, new_count, "picture object count mismatch")
 
        for count in xrange(1,10):    
            verify_new_picture = Picture.create(self.new_link)
            self.assertTrue(new_picture == verify_new_picture, 'new picture creation failed')
            self.assertTrue(new_picture == verify_new_picture, 'new picture creation failed')
            self.assertEqual(new_count, Picture.objects.all().count(), "picture object count mismatch")  
          
    def test_picture_create_picture_raises_exceptions(self):
        self.assertRaises(ValidationError, Picture.create, self.bad_link)
        self.bad_link = 'http://stackoverflow.com' 
        self.assertRaises(IOError, Picture.create, self.bad_link) 
    
    def test_picture_picture_link_in_size(self):
        pic = Picture.create("http://farm9.staticflickr.com/8366/8558127738_f2e5da9765.jpg")
        link_s = "http://farm9.staticflickr.com/8366/8558127738_f2e5da9765_s.jpg"
        link_q = "http://farm9.staticflickr.com/8366/8558127738_f2e5da9765_q.jpg"
        size_link = pic.picture_link_in_size("s")
        self.assertEqual(link_s, size_link, "Picture_link_in_size returns wrong with %s" % size_link)
        size_link = pic.picture_link_in_size("q")
        self.assertEqual(link_q, size_link, "Picture_link_in_size returns wrong with %s" % size_link)
        
    def test_picture_change_to_valid_link(self):
        old_link = self.picture.link
        self.picture.change_link(self.new_link);
        # self.picture must have gotten its link updated
        self.assertEqual(self.picture.link, self.new_link, 'link update failed')
        # database should have now 2 seperate pictures, one with old link
        Picture.objects.get(link=old_link)
        # and one with new link
        new_picture = Picture.objects.get(link = self.new_link)
        # and deep comparison must pass
        self.assertTrue(new_picture == self.picture, 'link update failed')
    
    def test_picture_change_to_bad_links(self):
        self.assertRaises(ValidationError, self.picture.change_link, self.bad_link)       
        # a valid link but does not point to a pic
        self.bad_link = 'http://stackoverflow.com'
        self.assertRaises(IOError, self.picture.change_link, self.bad_link)
                
    #Tests for page class
    def test_picture_create_page(self):
        self.assertQuerysetEqual( Page.objects.all().filter(text='space'), ['space'], attrgetter('text') )
        self.assertRaises(Exception, Page.create, self.too_long_caption )
        page = Page.create(self.new_text)
        del page

    def test_page_add_picture_without_caption(self):
        old_picture_count = self.page.pictures.count()
        old_section_count = Section.objects.all().count()
        self.new_picture = Picture.create(self.new_link)
        self.page.add_picture(self.new_picture) # must create a new section
        new_picture_count = self.page.pictures.count()
        new_section_count = Section.objects.all().count()
        self.assertEqual(old_picture_count + 1, new_picture_count, 'add picture failed')
        self.assertEqual(old_section_count + 1, new_section_count, 'add picture failed')            
        self.page.pictures.get(link=self.new_link) # throws exception if not found
        Section.objects.get(picture = self.new_picture, page = self.page, caption = None)
    
    #def test_page_add_picture_with_caption(self, caption=None):
    #    if caption != None:
    #        self.section_caption = caption
    #    old_picture_count = self.page.pictures.count()
    #    old_section_count = Section.objects.all().count()
    #    self.new_picture = Picture.create(self.new_link)
    #    self.page.add_picture(self.new_picture, self.section_caption) # must create a new section
    #    new_picture_count = self.page.pictures.count()
    #    new_section_count = Section.objects.all().count()
    #    self.assertEqual(old_picture_count + 1, new_picture_count, 'add picture failed')
    #    self.assertEqual(old_section_count + 1, new_section_count, 'add picture failed')            
    #    Section.objects.get(picture = self.new_picture, page = self.page, caption = self.section_caption)
    #    self.page.pictures.get(link=self.new_link) # throws exception if not found

    def test_page_add_picture_with_too_long_caption(self):
        with self.assertRaises( Exception ):
            self.test_page_add_picture_with_caption(self.too_long_caption)
        
    def test_page_add_same_picture_with_caption_many_times_to_page(self):
        # create 1 picture
        old_picture_count = Picture.objects.all().count()
        self.new_picture = Picture.create(self.new_link)
        new_picture_count = Picture.objects.all().count()
        self.assertEqual(old_picture_count + 1, new_picture_count, 'create picture failed')
        # add the same picture with same caption to the same page
        # check for number of pictures and sections the page has each time
        for count in xrange(1,10):
            old_picture_count = self.page.pictures.count()
            old_section_count = Section.objects.filter(picture = self.new_picture, page = self.page, caption = self.section_caption).count()
            self.page.add_picture(self.new_picture, self.section_caption) # must create a new section
            new_picture_count = self.page.pictures.count()
            new_section_count = Section.objects.filter(picture = self.new_picture, page = self.page, caption = self.section_caption).count()
            self.assertEqual(old_picture_count + 1, new_picture_count, 'adding the same picture with caption to the same page failed')
            self.assertEqual(old_section_count + 1, new_section_count, 'adding the same picture with caption to the same page failed')

    def test_page_remove_picture(self):
        self.test_page_add_picture_without_caption()
        old_picture_count = self.page.pictures.count()
        self.page.remove_picture(self.new_picture);
        new_picture_count = self.page.pictures.count()
        self.assertEqual(old_picture_count, new_picture_count + 1, 'remove picture failed')      
        with self.assertRaises( Picture.DoesNotExist ):
            self.page.pictures.get(link=self.new_link)
      
    def test_page_change_page_text(self):
        self.assertQuerysetEqual( Page.objects.filter(text='space'), ['space'], attrgetter('text'))
        self.page.change_page_text('Some photos')
        self.assertQuerysetEqual( Page.objects.filter(text='space'), [], attrgetter('text'))
        self.assertQuerysetEqual( Page.objects.filter(text='Some photos'), ['Some photos'], attrgetter('text'))
        
    #Tests for album class
    #def test_album_create_album(self):
    #    self.assertQuerysetEqual(Album.objects.get(title='My photo album').pages.all(), [u'space', u'yes'], attrgetter('text') )
    #    self.assertRaises(Exception, Album.create, 'raise exception', 'page text')
    #    album = Album.create(self.new_text, 'page text', self.profile)
    #    verify_album = Album.objects.get(title__icontains=self.new_text)
    #    self.assertEqual(album, verify_album, 'album creation failed')
        
    #def test_album_add_page(self):
    #    old_page_count = self.album.pages.count()
    #    new_page = Page.create(self.new_text)
    #    self.album.add_page(new_page)
    #    new_page_verification = self.album.pages.get(pk=new_page.pk)
    #    self.assertEqual(old_page_count+1, self.album.pages.count(), 'adding page failed')
    #    self.assertEqual(new_page, new_page_verification, 'adding page failed')
    #    return new_page
    
    #def test_add_same_page_to_the_same_album(self):
    #    # currently, it is allowed to add the same page over the album
    #    for count in xrange(1,10):
    #        old_page_count = self.album.pages.count()
    #        self.test_album_add_page()
    #        self.assertEqual(old_page_count+1, self.album.pages.count(), 'adding the same page failed')
    
    #def test_album_remove_the_only_page(self):
    #    # try to remove the only page in the album
    #    old_count = self.album.pages.count()
    #    self.assertNotEqual(old_count, 0, 'album page count should not be 0')
    #    present = self.album.is_page_present(self.page)
    #    self.assertEqual(present, True, 'album is missing a specific page to start with')        
    #    verify_presence = self.album.is_page_present(self.page)
    #    self.assertTrue(present == verify_presence, 'test_album_remove_page failed, the only page should remain in the album')
    #    new_count = self.album.pages.count()
    #    self.assertEqual(old_count, new_count, 'test_album_remove_page failed, should have the same page count')
    
    #def test_album_remove_many_pages(self): 
    #    count = 10
    #    old_count = self.album.pages.count()
    #    added_pages = []
    #    for i in xrange(1,count+1):
    #        added_pages.append( self.test_album_add_page() )
    #    
    #    ten_plus_count = self.album.pages.count()
    #    self.assertEqual(ten_plus_count, old_count + count , 'album page count mismatch')
    #
    #    for i in xrange(1,count+1):
    #        the_page = added_pages[i-1]
    #        self.assertNotEqual(old_count, 0, 'album page count should not be 0')
    #        present = self.album.is_page_present(the_page)
    #        self.assertEqual(present, True, 'album is missing a specific page to start with')
    #        self.album.remove_page(the_page)        
    #        verify_presence = self.album.is_page_present(the_page)
    #        self.assertTrue(present != verify_presence, 'test_album_remove_page failed, the only page remained in the album')
    #        new_count = self.album.pages.count()
    #        self.assertEqual(ten_plus_count - 1, new_count, 'test_album_remove_page failed, should have the same page count')
    #        ten_plus_count -= 1
       
        
    #def test_album_change_album_title(self):
    #    self.new_album_title = 'New album title'
    #    self.album.change_album_title(self.new_album_title)
    #    self.assertEqual(Album.objects.get(title=self.new_album_title).title, self.new_album_title)

    def test_section_create_section(self):
        old_count = Section.objects.all().count()
        self.section = Section(picture = self.picture, page = self.page, caption = self.section_caption)
        self.section.save()
        new_count = Section.objects.all().count()
        self.assertEqual(old_count + 1, new_count, 'add section failed')      
    
    def test_section_delete_section(self):
        self.test_section_create_section()
        old_count = Section.objects.all().count()
        self.section.delete()
        new_count = Section.objects.all().count()
        self.assertEqual(old_count, new_count  + 1, 'delete section failed')      

    def test_section_change_caption(self):
        self.test_section_create_section()
        self.new_caption = 'new caption'
        old_caption = self.section.caption
        self.section.change_caption(self.new_caption)

        with self.assertRaises( Section.DoesNotExist ):
            print Section.objects.get(caption=old_caption)
        verify_section = Section.objects.get(caption=self.new_caption)
        self.assertEqual(verify_section, self.section, 'change caption in section failed')
'''
      
import flickrapi
from django.utils import simplejson
class FlickrTests(TestCase, unittest.TestCase):

    def setUp(self):
        # Initialize a Django test client
        self.client = Client()
        self.factory = RequestFactory()
        # we do know that test db is recreated clean each time we run a single unit test
        Album.objects.all().delete()
        Page.objects.all().delete()
        Section.objects.all().delete()
        Picture.objects.all().delete()
        self.user = User.objects.create_user("username", "email@testi.fi", "123456")
        self.user.save()
        self.profile = Profile.create(self.user)
        self.album = Album.create('Album for delete_album tests', 'page_text', self.profile)
        self.search_text = 'cat'
        self.request_url = '/albums/' + str(self.album.id) + '/pages/index/'
        self.except_these = ['400.html']
        self.client.login(username='username', password='123456')
    
    def _verify_with_flickrs_own(self, views_response, use_empty_json_as_expected_result = False):
        if use_empty_json_as_expected_result:
            self.assertRaises(ValueError, simplejson.loads, views_response.content)
        else: # we expect a healty JSON object from views_response
            decoded_view_response = simplejson.loads(views_response.content)

        # use FlickrAPI itself to make the same search
        flickr_response_data = []
        if not use_empty_json_as_expected_result and self.search_text != None and len(self.search_text) and not self.search_text.isspace():
            api_key = 'ed454f98b03899ecdb00a39162f775f1'
            flickr = flickrapi.FlickrAPI(api_key)
            flickr_response = flickr.photos_search(text=self.search_text, per_page=FLICKR_SEARCH_RESULT_COUNT)
            for photo in flickr_response.iter('photo'):
                url = 'http://farm' + photo.get('farm') + '.staticflickr.com/' + photo.get('server') + '/' + photo.get('id') + '_' + photo.get('secret') + '_q.jpg'
                flickr_response_data.append(url)
            
        # compare the above two results
        if not use_empty_json_as_expected_result:
            self.assertEqual(decoded_view_response, flickr_response_data, '_verify_with_flickrs_own failed comparing Flickrs own response vs. search_flickrs own JSON')

    def _test_search_flickr_with_mock(self):
        # use the view with a one word valid request
        # self.factory produces mocked request objects
        request = self.factory.get(self.request_url, {'text' : self.search_text}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        request.session = {}
        views_response = search_flickr(request)
        self._verify_with_flickrs_own(views_response)
  
    # using mocked request objects in search_flickr view
    def test_search_flickr_with_proper_one_word_argument(self):
        self._test_search_flickr_with_mock()

    def test_search_flickr_with_proper_two_word_arguments(self):
        self.search_text = 'white cat'
        self._test_search_flickr_with_mock()
        
    def _form_data(self, search_text = None):
        data = {}
        if search_text != None:
            data['text'] = search_text
        return data
    
    def _test_search_flickr_with_get(self, expected_status_code):
        self.request_url = '/pictures/search_flickr/'
        data = self._form_data(self.search_text)
        response = self.client.get(self.request_url, data, follow=True)
        self.assertEquals(response.status_code, expected_status_code, "_test_search_flickr_with_get returns response.status_code %s while expected is %s" % (response.status_code, expected_status_code))
        return response
    
    def _test_search_flickr_with_get_ajax(self, expected_status_code):
        self.request_url = '/pictures/search_flickr/'
        data = self._form_data(self.search_text)
        response = self.client.get(self.request_url, data, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, expected_status_code, "_test_search_flickr_with_get returns response.status_code %s while expected is %s" % (response.status_code, expected_status_code))
        self._verify_with_flickrs_own(response)
        return response

    #def test_search_flickr_success_with_get_ajax(self):
    #    self.search_text = 'cat'
    #    self._test_search_flickr_with_get_ajax(expected_status_code=200)
    #    
    #    self.search_text = 'white cat'
    #    self._test_search_flickr_with_get_ajax(expected_status_code=200)
        
    # this cookie check function can be duplicated for other view functions
    # it is not duplicated for now, as we don't know the future use of cookie returns from views
    def _test_cookie_valid_search_string_warning(self, response):
        messages_cookie = response.cookies.get('messages')
        re1='.*?'    # Non-greedy match on filler
        re2='(Please)'    # Word 1
        re3='.*?'    # Non-greedy match on filler
        re4='(pass)'    # Word 2
        re5='.*?'    # Non-greedy match on filler
        re6='(valid)'    # Word 3
        re7='.*?'    # Non-greedy match on filler
        re8='(search)'    # Word 4
        re9='.*?'    # Non-greedy match on filler
        re10='(string)'    # Word 5
        re11='.*?'    # Non-greedy match on filler
        re12='(for)'    # Word 6
        re13='.*?'    # Non-greedy match on filler
        re14='(Flickr)'    # Word 7
        
        rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12+re13+re14,re.IGNORECASE|re.DOTALL)
        m = rg.search(messages_cookie.__str__())
        self.assertTrue(len(m.group(1)), '_test_cookie failed') 
        self.assertTrue(len(m.group(2)), '_test_cookie failed')
        self.assertTrue(len(m.group(3)), '_test_cookie failed')
        self.assertTrue(len(m.group(4)), '_test_cookie failed')
        self.assertTrue(len(m.group(5)), '_test_cookie failed')
        self.assertTrue(len(m.group(6)), '_test_cookie failed')
        self.assertTrue(len(m.group(7)), '_test_cookie failed')
        
    def test_search_flickr_failure_with_get(self):
        self.search_text = 'cat'
        self._test_search_flickr_with_get(expected_status_code=400)
        
        self.search_text = 'white cat'
        self._test_search_flickr_with_get(expected_status_code=400)
        
        self.search_text = ''
        self._test_search_flickr_with_get(expected_status_code=400)
        
        self.search_text = None
        self._test_search_flickr_with_get(expected_status_code=400)
         
        self.search_text = '   '
        self._test_search_flickr_with_get(expected_status_code=400)
        
    def test_search_flickr_failure_with_get_ajax(self):
        self.search_text = ''
        response = self._test_search_flickr_with_get_ajax(expected_status_code=200)
        self._test_cookie_valid_search_string_warning(response)
        
        self.search_text = None
        response = self._test_search_flickr_with_get_ajax(expected_status_code=200)
        self._test_cookie_valid_search_string_warning(response)
         
        self.search_text = '   '
        response = self._test_search_flickr_with_get_ajax(expected_status_code=200)
        self._test_cookie_valid_search_string_warning(response)        
        
    def _test_search_flickr_with_post(self, expected_status_code):
        self.request_url = '/pictures/search_flickr/'
        data = self._form_data(self.search_text)
        response = self.client.post(self.request_url, data, follow=True)
        self.assertEquals(response.status_code, expected_status_code, "_test_search_flickr_with_post returns response.status_code %s while expected is %s" % (response.status_code, expected_status_code))
        _test_no_template_used(self,response, except_these = self.except_these)        
        self._verify_with_flickrs_own(response, use_empty_json_as_expected_result = True)
        return response
    
    def test_search_flickr_failure_with_post(self):
        self.search_text = 'fly'
        self._test_search_flickr_with_post(expected_status_code=400)
        
