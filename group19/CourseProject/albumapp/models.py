from django.db import models
from StringIO import StringIO
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from PIL import Image
from django.contrib.auth.models import User

class Picture(models.Model):
    link = models.URLField(primary_key = True)
    
    # This method should be used to provide custom model validation, and to modify attributes on your model if desired.
    def clean(self):
        # check if the self.link has a valid url
        validator = URLValidator(verify_exists=True)
        validator(self.link)  # this will throw a validation error if needed
        
        # check if the picture at self.link is a valid picture
        # yes, we use additional Python Imaging Library!
        request = requests.get(self.link)
        image = Image.open(StringIO(request.content)) # this would throw IOError if not image
        del image
        
        
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Picture, self).save(*args, **kwargs) # Call the "real" save() method.
        
    #usage: as a constructor, e.g. picture = Picture.create("http://test.fi/pic.jpg")
    @classmethod
    def create(cls, url):
        try:
            picture = cls.objects.get(link = url)
        except cls.DoesNotExist:
            picture = cls(link=url)
            picture.save() # will do verification (and throw exception if needed) then saves to db
        return picture


    #Separate change functions for different attributes, atm I see them used as such from the UI   
    def change_link(self, new_link):
        self.link = new_link
        self.save()
        
    def picture_link_in_size(self, size):
        link = self.link
        link_end = link[link.__len__()-3:link.__len__()]
        if size != "":
            new_link_end = "_"+size+"."+link_end+""
            new_link = link[0:link.__len__()-4] + new_link_end
        else:
            new_link = link
        return new_link
        
    def __unicode__(self):
        return 'Picture with url %s' % (self.link)

class Profile(models.Model):
    user = models.OneToOneField(User)
    pictures = models.ManyToManyField(Picture)

    @classmethod
    def create(cls, user):
        profile = cls(user=user)
        profile.save()
        return profile

class Template(models.Model):
    size = models.CharField(max_length=2) #size for Flickr urls
    priority = models.IntegerField()
     
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Page, self).save(*args, **kwargs) # Call the "real" save() method.
    
    #usage: as a constructor, e.g. Template = Template.create("large")
    @classmethod
    def create(cls, size, priority):
        template = cls(size = size, priority = priority)
        template.save() # will do verification in .clean (and throw exception if needed) then saves to db
        return template

class Layout(models.Model):
    templates = models.ManyToManyField(Template)
            
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Page, self).save(*args, **kwargs) # Call the "real" save() method.
    
    #usage: as a constructor
    @classmethod
    def create(cls, templates, rows, columns):
        layout = cls(templates = templates, rows = rows, columns = columns)
        layout.save() # will do verification in .clean (and throw exception if needed) then saves to db
        return layout
            
class Page(models.Model):
    text =  models.TextField(max_length=150, blank=True)
    # allow blank pages, you can create pages e.g. "cover-pages" for many albums
    pictures = models.ManyToManyField(Picture, blank=True, null=True, through='Section')
    layout = models.ForeignKey(Layout)

    # This method should be used to provide custom model validation, and to modify attributes on your model if desired.
    def clean(self):
        # do custom verifications here or throw intentional exceptions for unit testing
        if self.text.__str__().__len__() > 150:
            raise Exception('New text too long!')
             
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Page, self).save(*args, **kwargs) # Call the "real" save() method.

    #usage: as a constructor, e.g. page = Page.create("That summer day")
    @classmethod
    def create(cls, text, layout):
        page = cls(text=text, layout=layout) # a blank page, with optional text 
        page.save() # will do verification in .clean (and throw exception if needed) then saves to db
        return page
         
    def add_picture(self, pict, text=None):
        Section.create(pict, self, text )
        
    def remove_picture(self, pict):
        section_to_delete = Section.objects.get(picture = pict, page = self)
        section_to_delete.delete()
        
    def change_page_text(self, new_text):
        self.text = new_text
        self.save()
        
    def set_layout(self, layout):
        self.layout = layout
        self.save()
        
    def __unicode__(self):
        return 'Page id %i with text %s and count of pictures %i' % (self.id, self.text, self.pictures.count())

class Section(models.Model):
    picture = models.ForeignKey(Picture)
    page = models.ForeignKey(Page)
    caption = models.TextField(max_length=200, blank=True, null=True)
    priority = models.IntegerField()

    # This method should be used to provide custom model validation, and to modify attributes on your model if desired.
    def clean(self):
        # do custom verifications here or throw intentional exceptions for unit testing
        if self.caption.__str__().__len__() > 200:
            raise Exception('Caption too long')
        
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Section, self).save(*args, **kwargs) # Call the "real" save() method.

    #usage: as a constructor, e.g. page = Page.create("That summer day")
    @classmethod
    def create(cls, _picture, _page, _caption, _priority):
        section = cls(picture= _picture, page= _page, caption= _caption, priority = _priority) # a blank page, with optional text
        section.save() # will do verification in .clean (and throw exception if needed) then saves to db
        return section

    def change_caption(self, new_text):
        self.caption = new_text
        self.save()
        
    def __unicode__(self):
        return 'Section id %i with caption %s' % (self.id, self.caption)
      
class Album(models.Model):
    owner = models.ForeignKey(Profile)
    title = models.CharField(max_length=100, blank=False)
    pages = models.ManyToManyField(Page)

    # This method should be used to provide custom model validation, and to modify attributes on your model if desired.
    def clean(self):
        # do custom verifications here or throw intentional exceptions for unit testing
        if self.title == 'raise exception':
            raise Exception('album exception')
             
    def save(self, *args, **kwargs):
        self.full_clean()  # do custom verification via custom .clean() method
        super(Album, self).save(*args, **kwargs) # Call the "real" save() method.
  
    #usage: as a constructor, e.g. album = Album.create("My family portrait"), it also does the validation logic
    @classmethod
    def create(cls, title, page_text, profile):
        try:
            layout = Layout.objects.get(id=1)
            page = Page.create(page_text, layout) # this creates the default first page for the album. we can use a default page_text, given from view, for every album e.g. "Your very first Album Page."
            album = cls(owner=profile, title=title)
            # will do verification in .clean (and throw exception if needed) then saves to db
            album.save() # the album title can't be blank, save for the first time to enable page adding. For testing purposes, blank=False is tested only with forms, direct accessing with blank string won't fail.
            album.pages.add(page)
            album.save() # will do verification in .clean (and throw exception if needed) then saves to db
        except ValidationError:
            if page.id != None: 
                page.delete()
            if album.id != None:
                album.delete()
            raise 
        return album

    def add_page(self, page):
        self.pages.add(page)
        self.save()
        
    def remove_page(self, page):
        if self.pages.count() > 1:
            self.pages.remove(page)
            self.save()            
        else:
            raise Exception('The last page can not be deleted!')
        #page.delete() #if pages are not independent of albums, uncomment
        
    def change_album_title(self, new_title):
        self.title = new_title
        self.save()
        
    def is_page_present(self, page):
        result = True
        try:
            self.pages.get(pk = page.pk)
        except:
            result = False
        return result
    
    def __unicode__(self):
        return 'Album id %i with title %s and count of pages %i' % (self.id, self.title, self.pages.count())
    
