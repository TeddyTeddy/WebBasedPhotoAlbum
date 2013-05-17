from django.conf.urls import patterns, include, url
from albumapp import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'CourseProject.views.home', name='home'),
    # url(r'^CourseProject/', include('CourseProject.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^albums/index/', views.album_index, name='index'),
    url(r'^albums/create_album/', views.create_album, name='create_album'),
    url(r'^albums/change_page_text/', views.change_page_text, name='change_page_text'),
    url(r'^albums/add_page_to_album/', views.add_page_to_album, name='add_page_to_album'),
    url(r'^albums/change_picture_link/', views.change_picture_link, name='change_picture_link'), 
    url(r'^albums/change_section_captions/', views.change_section_captions, name='change_section_captions'),
    url(r'^albums/create_sections/', views.create_sections, name='create_sections'),
    url(r'^albums/remove_sections/', views.remove_sections, name='remove_sections'),
    url(r'^admin/$', include(admin.site.urls)),
    url(r'^albums/index/$', views.album_index, name='index'),
    url(r'^albums/create_album/$', views.create_album, name='create_album'),
    url(r'^albums/delete_album/$', views.delete_album, name='delete_album'),
    url(r'^albums/save_page/$', views.save_page, name='save_page'),
    url(r'^albums/change_page_text/$', views.change_page_text, name='change_page_text'),
    url(r'^albums/change_album_title/$', views.change_album_title, name='change_album_title'),
    url(r'^albums/(\d+)/add_page_to_album/$', views.add_page_to_album, name='add_page_to_album'),
    url(r'^albums/remove_page_from_album/', views.remove_page_from_album, name='remove_page_from_album'),
    url(r'^albums/(\d+)/pages/index/$', views.page_index, name='page_index'),
    url(r'^albums/(\d+)/pages/(\d+)/show/$', views.show_page, name='page_index'),
    url(r'^albums/change_picture_link/$', views.change_picture_link, name='change_picture_link'), 
    url(r'^pages/change_section_captions/$', views.change_section_captions, name='change_section_captions'),
    url(r'^pages/create_sections/$', views.create_sections, name='create_sections'),
    url(r'^pages/remove_sections/$', views.remove_sections, name='remove_sections'),
    url(r'^pages/select_page_layout/$', views.select_page_layout, name='select_page_layout'),
    url(r'^pictures/search_flickr/', views.search_flickr, name='search_flickr'),
    url(r'^pictures/add_picture_url_to_database/', views.add_picture_url_to_database, name='add_picture_url_to_database'),
    url(r'^enter/', views.login_page, name='login_page'),
    url(r'^register/', views.register, name='register'),
    url(r'^login/', views.log_user_in, name='log_user_in'),
    url(r'^logout/', views.log_user_out, name='log_user_out'),
    url(r'^link/', views.view_public_link, name='view_public_link'),
    url(r'^get_link/$', views.get_public_link, name='get_public_link'),
)
