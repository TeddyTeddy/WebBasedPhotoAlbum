from models import Picture, Page, Album, Profile
import flickrapi
import random

from django.contrib.auth.models import User

flickr_API_key = '53ff7065a15733bf818661273e22a264'
flickr_API_key_secret = 'a2fe3c93d5193c04'
default_album_count = 10
default_photo_count = 100

class DatabaseContentCreator:
    
    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(api_key = flickr_API_key, secret = flickr_API_key_secret)
        self.create_profiles()
    
    def create_one_user_profile(self, username, email, password):
        user = User.objects.create_user(username, email, password)
        user.save()
        profile = Profile.create(user)
        return profile
    
    def create_profiles(self):
        self.create_one_user_profile('jaakko', 'jaakko@jaakko.com', 'newpass' )
        self.create_one_user_profile('mikko1', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko2', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko3', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko4', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko5', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko6', 'mikko@mikko.com', 'newpass' )
        self.create_one_user_profile('mikko7', 'mikko@mikko.com', 'newpass' )
    
    def pick_a_random_profile(self):
        profiles = Profile.objects.all()
        random_index = random.randrange(0, profiles.count())
        return profiles[random_index]

    def create_photos(self, photo_count = default_photo_count):
        count = 1;
        for photo in self.flickr.walk(text='butteryfly', content_type='1', media='photos', per_page=photo_count):
            farm_id = photo.get('farm')
            server_id = photo.get('server')
            _id = photo.get('id')
            secret = photo.get('secret')
            url = 'http://farm' + farm_id + '.staticflickr.com/' + server_id + '/' + _id + '_' + secret + '.jpg'
            print url
            Picture.create(url)
            count +=1
            if count > photo_count:
                break  
        return self
    
    def create_one_album(self, album_title = 'Album'):
        pictures = Picture.objects.all()
        album = Album.create(album_title, 'First Page', self.pick_a_random_profile())
        page_count = random.randrange(5,101) # 5 <= page_count <= 100
        for i in xrange(1, page_count):
            text = 'Page ' + i.__str__()
            page = Page.create(text)
            picture_count = random.randrange(1,5) # 1 <= picture_count <= 4
            for j in xrange(1, picture_count):
                # pick a random picture from database and add it to a page
                random_index = random.randrange(0, pictures.count())
                random_picture = pictures[random_index]
                page.add_picture(random_picture, j.__str__())  
            # Page ready to be added to album
            album.add_page(page)
        return self
        
    def create_albums(self, album_count = default_album_count, create_photos = True):
        if create_photos:
            self.create_photos() # first extend the photo
        for i in xrange(1, album_count):
            album_title = 'Album No ' + i.__str__()
            self.create_one_album(album_title)
        return self

    '''
    # Returns the path to given filename                                                                                                                           
    def _get_path_to_fixture(self, filename):
        return os.path.join(os.path.dirname(__file__), 'fixtures/' + filename).replace('\\','/')


    I spent a lot of time with this. Wanna keep it in case it gets useful.
    I used http://txt2re.com/index-python.php 
    
    def create_database_fixture(self, album_count = default_album_count, create_photos = True):
        path_to_fixture = self._get_path_to_fixture('initial_data.xml')
        print 'writing to fixture: ', path_to_fixture
        out = open(path_to_fixture, 'w')
        out.write('<?xml version="1.0" encoding="utf-8"?>')
        out.write('<django-objects version="1.0">')
        # self.create_albums(album_count, create_photos)

        for picture in Picture.objects.all():
            picture_data = serializers.serialize('xml', [picture])
            re1='(<\\?xml version="1\\.0" encoding="utf-8"\\?>\n)'     # Tag 1
            re2='(<django-objects version="1\\.0">)'    # Tag 2
            re3='(.*?)'    # Non-greedy match on filler
            re4='(<\\/django-objects>)'    # Tag 3
            rg = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)
            m = rg.search(picture_data)
            print 'writing', m.group(3)
            out.write(m.group(3))
        out.flush()
        
        for page in Page.objects.all():     
            page_data = serializers.serialize('xml', [page])
            # print 'writing', page_data 
            out.write(page_data)
        out.flush()
        
        for section in Section.objects.all():     
            section_data = serializers.serialize('xml', [section])
            # print 'writing', section_data
            out.write(section_data)
        out.flush()
   
        for album in Album.objects.all():     
            album_data = serializers.serialize('xml', [album])
            # print 'writing', album_data
            out.write(album_data)

        out.write('</django-objects>')
        out.close()
        return self
'''
        
    