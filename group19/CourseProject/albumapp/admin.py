from django.contrib import admin
from albumapp.models import Picture, Page, Album, Section

# these are just there to have a kick start, they will change for sure
class PictureAdmin(admin.ModelAdmin):
    list_filter = ('link',)
    
class PageAdmin(admin.ModelAdmin):
    list_filter = ('text',) 

class SectionAdmin(admin.ModelAdmin):
    list_filter = ('id', 'caption',)  

class ProfileAdmin(admin.ModelAdmin):
    list_filter = ('user')
    
class AlbumAdmin(admin.ModelAdmin):
    list_filter = ('title', 'owner')   
    
admin.site.register(Picture, PictureAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Album, AlbumAdmin)