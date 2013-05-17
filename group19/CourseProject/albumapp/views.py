from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.shortcuts import redirect
from albumapp.models import Picture, Section, Page, Album, Profile, Layout, Template
from django.contrib import messages
import xml.etree.ElementTree as ET
import flickrapi
from django.views.decorators.csrf import csrf_protect
from django.utils import simplejson
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import base64

#CONSTANTS
FLICKR_SEARCH_RESULT_COUNT = 60 #Defines the amount of returned flickr results

#ALBUM ACTIONS

@login_required
def album_index(request):
    return render_to_response('albums/index.html', {
        'album_list': Album.objects.order_by('id').filter(owner=Profile.objects.get(user=request.user)),
        'picture_list': Profile.objects.get(user=request.user).pictures.all(),
    }, context_instance=RequestContext(request))

@csrf_protect
@login_required
def create_album(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        page_text = request.POST.get('page_text', '')
        try:
            Album.create(title, page_text, Profile.objects.get(user=request.user))
            messages.info(request, 'Album created succesfully!') 
        except Exception as e:
            messages.error(request, e.__str__())   
        return redirect("/albums/index/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))


@csrf_protect
@login_required
def delete_album(request):
    if request.method == 'POST':
        try:
            album_id = request.POST.get('album_id')
            album = get_object_or_404(Album, pk=album_id)
            if album.owner.user == request.user:
                album.delete()
                messages.info(request, 'Album deleted!')
            else:
                return HttpResponseBadRequest(render_to_response('400.html'))
        except Exception as e:
            messages.error(request, e.__str__()) 
        return redirect("/albums/index/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect
@login_required
def add_page_to_album(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        album_id = request.POST.get('album_id')
        if album_id and album_id != "" and album_id.isdigit():
            album = get_object_or_404(Album, pk=album_id)
            layout = get_object_or_404(Layout, pk=1)
            if album.owner.user == request.user:
                try:
                    page = Page.create(title, layout)  
                    try:
                        album.add_page(page)
                        messages.info(request, 'Page created')
                        return redirect('/albums/'+album_id+'/pages/'+str(page.id)+'/show/')
                    except Exception as e:
                        page.delete()  # fully commit or roll back
                        messages.error(request, e.__str__()) 
                except Exception as e:
                    messages.error(request, e.__str__())
                return redirect('/albums/'+album_id+'/pages/index/')
            else:
                return HttpResponseBadRequest(render_to_response('400.html'))
        else:
            raise Http404
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect
@login_required
def remove_page_from_album(request):
    if request.method == 'POST':
        album_id = request.POST.get('album_id')
        page_id = request.POST.get('page_id')
        if (album_id and page_id) and (album_id != "" and page_id != "") and (page_id.isdigit() and album_id.isdigit()):  
            page = get_object_or_404(Page, pk=page_id)
            album = get_object_or_404(Album, pk=album_id)
            if album.owner.user == request.user:
                try:
                    album.remove_page(page)
                    messages.info(request, 'Page removed')
                except Exception as e:
                    messages.error(request, e.__str__())
                    return redirect('/albums/'+album_id+'/pages/index/')
                return redirect('/albums/'+album_id+'/pages/index/')
            else:
                return HttpResponseBadRequest(render_to_response('400.html'))
        else:
            raise Http404
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect
@login_required
def change_album_title(request):
    if request.method == 'POST':
        album_id = request.POST.get('album_id')
        new_album_title = request.POST.get('new_album_title')
        if album_id and album_id != "" and album_id.isdigit():
            album = get_object_or_404(Album, pk=album_id)
        else:
            raise Http404
        try:
            if request.user == album.owner.user:
                album.change_album_title(new_album_title)
                messages.info(request, 'Album title changed')
            else:
                return HttpResponseBadRequest(render_to_response('400.html')) 
        except Exception as e:
            messages.error(request, e.__str__())
        return redirect("/albums/index/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))
    
# PAGE ACTIONS
@login_required
def page_index(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    if request.user == album.owner.user:
        return render_to_response('pages/index.html', {
            'page_list': album.pages.all(),
            'album_id': album.id,
            'picture_list': Picture.objects.all(),
        }, context_instance=RequestContext(request))
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))    

@login_required
def show_page(request, album_id, page_id):
    album = get_object_or_404(Album, pk=album_id)
    if request.user == album.owner.user:
        page = get_object_or_404(Page, pk=page_id)
        return render_to_response('pages/show.html', {
            'page_list': album.pages.all(),
            'album_id': album.id,
            'picture_list': Picture.objects.all(),
            'section_list': Section.objects.filter(page=page),
            'page': page,
            'layouts': Layout.objects.all()
        }, context_instance=RequestContext(request)) 
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect   
@login_required
def select_page_layout(request):
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        new_layout_id = request.POST.get('layout_id')
        album_id = request.POST.get('album_id')
        if (album_id and page_id and new_layout_id) and (album_id != "" and page_id != "" and new_layout_id != "" ) and (album_id.isdigit() and page_id.isdigit() and new_layout_id.isdigit()):
            page = get_object_or_404(Page, pk=page_id)
            layout = get_object_or_404(Layout, pk=new_layout_id)
            album = get_object_or_404(Album, pk=album_id)
        else:
            raise Http404
        try:
            if request.user == album.owner.user:
                page.set_layout(layout)
                messages.info(request, 'Layout changed!')
            else:
                return HttpResponseBadRequest(render_to_response('400.html')) 
        except Exception as e:
            messages.error(request, e.__str__())
        return redirect("/albums/"+album_id+"/pages/"+page_id+"/show/")       
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))    

@csrf_protect   
@login_required
def save_page(request):
    if request.method == 'POST':
        picture_list = request.POST.getlist('picture_pk')
        captions = request.POST.getlist('section_caption')
        section_list = request.POST.getlist('section_pk')
        section_change_list = request.POST.getlist('section_change_pk')
        album_id = request.POST.get('album_id')
        page_id = request.POST.get('page_id')
        create_secs = False
        for pic in picture_list:
            if pic != "":
                create_secs = True
        remove_sections(request, section_list)
        if create_secs:
            create_sections(request, picture_list, captions)
        change_section_captions(request, captions, section_change_list)
        change_page_text(request)
        return redirect("/albums/"+album_id+"/pages/"+page_id+"/show/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect   
@login_required
def change_page_text(request):
    if request.method == 'POST':
        album_id = request.POST.get('album_id')
        page_id = request.POST.get('page_id')
        new_page_text = request.POST.get('new_page_text')
        if (album_id and page_id) and (album_id != "" and page_id != "") and (album_id.isdigit() and page_id.isdigit()):
            page = get_object_or_404(Page, pk=page_id)
            album = get_object_or_404(Album, pk=album_id)
        else:
            raise Http404
        try:
            if album.owner.user == request.user and album.pages.filter(pk=page_id).count() == 1:
                if page.text != new_page_text:
                    page.change_page_text(new_page_text)
                    messages.info(request, 'Page text changed')
            else:
                return HttpResponseBadRequest(render_to_response('400.html')) 
        except Exception as e:
            messages.error(request, e.__str__()) 
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))
    
@csrf_protect
@login_required
def create_sections(request, picture_list, captions):
    if request.method == 'POST':   
        page_pk = request.POST.get('page_id')
        if page_pk and page_pk != "" and page_pk.isdigit():  
            page = get_object_or_404(Page, pk=page_pk)
        else:
            raise Http404
        count = 0
        for i in range(len(picture_list)):
            picture_pk = picture_list[i]
            priority = i+1
            section_caption = captions[i]
            if picture_pk != None and picture_pk != "":
                picture = get_object_or_404(Picture, pk=picture_pk)
                try:
                    Section.create(picture, page, section_caption, priority)
                    count = count + 1
                except Exception as e:
                    messages.error(request, e.__str__())
        if count == 0:
            messages.error(request, "Zero sections created, please choose pictures!")
        else:
            messages.info(request, "Sections created: %d" % count)
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@csrf_protect
@login_required
def remove_sections(request, section_list):
    if request.method == 'POST': 
        for i in range(len(section_list)):
            section_pk = section_list[i]
            if section_pk and section_pk != "" and section_pk.isdigit():
                section = get_object_or_404(Section, pk=section_pk)
                section.delete()
            else:
                raise Http404       
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

#PICTURE ACTIONS   
@csrf_protect 
@login_required
def change_picture_link(request):
    if request.method == 'POST': 
        picture_pk = request.POST.get('picture_pk')
        pic_link = request.POST.get('pic_link')
        picture = get_object_or_404(Picture, pk=picture_pk)
        try:
            picture.change_link(pic_link)
            messages.info(request, 'Picture link changed.')
        except Exception as e:
            messages.error(request, e.__str__())    
        return redirect("/albums/index/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

#SECTION ACTIONS
@csrf_protect
@login_required
def change_section_captions(request, captions, section_change_list):
    if request.method == 'POST':
        count = 0
        for i in range(len(section_change_list)):
            section_pk = section_change_list[i]
            new_section_caption = captions[i]
            if section_pk and section_pk != "" and section_pk.isdigit(): 
                if section_pk != '0':       
                    section = get_object_or_404(Section, pk=section_pk)
                    old_caption = section.caption
                    try:
                        if new_section_caption != section.caption:
                            section.change_caption(new_section_caption)
                            count = count + 1
                    except Exception as e:
                        messages.error(request, '%s, Section with caption "%s" was not changed' % (e.__str__(), old_caption))
            else:
                raise Http404
        if count > 0:
            messages.info(request, 'Sections renamed: %d' % count)
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))
        
@csrf_protect 
@login_required
def add_picture_url_to_database(request):
    if request.is_ajax() and request.method == 'POST':
        url = request.POST.get('url')
        picture = Picture.create(url)
        #Profile.objects.get(user=request.user).pictures.add(picture)
        album_id = request.POST.get('album_id')
        return HttpResponse(200)
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

#FLIKCR ACTIONS
@login_required
def search_flickr(request):
    response_data = []
    if request.is_ajax() and request.method == 'GET':
        # we need to use Django Forms here to do form verification.
        search_text_valid = request.GET.__contains__('text') and request.GET.get('text') != '' and request.GET.get('text').isspace() == False
        if search_text_valid:
            text = request.GET.get('text')
            api_key = 'ed454f98b03899ecdb00a39162f775f1'
            flickr = flickrapi.FlickrAPI(api_key)
            response = flickr.photos_search(text=text, per_page=FLICKR_SEARCH_RESULT_COUNT)
            for photo in response.iter('photo'):
                url = 'http://farm' + photo.get('farm') + '.staticflickr.com/' + photo.get('server') + '/' + photo.get('id') + '_' + photo.get('secret') + '_q.jpg'
                response_data.append(url)
        else:
            messages.info(request, 'Please pass a valid search string for Flickr')
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

#LOGIN ACTIONS
def register(request):
    if request.method == 'POST':
        # we need a try catch block, in case post doesnt have the requested parameters: username, email, password
        # the checks below need to be replaced with Django Forms
        username = request.POST.get('username')
        if len(username) > 0 and username.isspace() == False:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect("/enter/")
            else:
                email = request.POST.get('email')
                password = request.POST.get('password')
                if len(password) < 1 or password.isspace():
                    messages.error(request, 'Invalid password.')
                    return redirect("/enter/")
                user = User.objects.create_user(username, email, password)
                user.save()
                Profile.create(user)
                messages.info(request, 'User succesfully created.')
                return redirect("/enter/")
        else:
            messages.error(request, 'Invalid username.')
            return redirect("/enter/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

def log_user_in(request):
    # missing Django Form usage
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                #User is now authenticated
                login(request, user)
                messages.info(request, 'You are now logged in.')
                return redirect("/albums/index/")
            else:
                messages.error(request, 'Account has been disabled!')
                return redirect("/enter/")
        else:
                messages.error(request, 'Login incorrect.')
                return redirect("/enter/")
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

@login_required
def log_user_out(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect("/enter/")

def login_page(request):
    profile_count = Profile.objects.count()  
    return render_to_response('login/index.html', { 'profile_count': profile_count },
    context_instance=RequestContext(request))

#PUBLIC LINK ACTIONS

@login_required
def get_public_link(request):
    album_id = request.POST.get('album_id')
    album = get_object_or_404(Album, pk=album_id)
    page_id = request.POST.get('page_id')
    if page_id == "F":
        page = album.pages.all()[0]
    else:
        page = get_object_or_404(Page, pk=page_id)
    if album.owner.user == request.user:
        link = generate_hash(request, album.id, page.id)
        if request.POST.get('operation') == "GET_LINK":
            messages.info(request, link)
            return redirect("/albums/index/")
        elif request.POST.get('operation') == "SHARE_TO_FACEBOOK":
            return redirect("http://www.facebook.com/sharer.php?u=" + link)
        else:
            return HttpResponseBadRequest(render_to_response('400.html'))
    else:
        return HttpResponseBadRequest(render_to_response('400.html'))

def view_public_link(request):
    hash = request.GET.get('url', '')
    try:
        values = base64.b64decode(hash).split("_")
        album_id = values[0]
        page_id = values[1]
        album = get_object_or_404(Album, pk=album_id)#album id exists
        page = get_object_or_404(Page, pk=page_id)#page id exists
        pages = album.pages.all()
        for i in range(len(pages)):
            if pages[i] == page:
                page_number = i+1
                if i == 0: 
                    prev_link = generate_hash(None, album.id, page.id) 
                    if len(pages) > 1:
                        next_link = generate_hash(None, album.id, pages[i+1].id)
                    else:
                        next_link = prev_link  
                elif i == len(pages)-1:
                    prev_link = generate_hash(None, album.id, pages[i-1].id)
                    next_link = generate_hash(None, album.id, page.id) 
                else:
                    next_link = generate_hash(None, album.id, pages[i+1].id) 
                    prev_link = generate_hash(None, album.id, pages[i-1].id) 
        return render_to_response('public_link.html', {
            'page_list': album.pages.all(),
            'album_id': album.id,
            'picture_list': Picture.objects.all(),
            'next_link': next_link,
            'prev_link': prev_link,
            'section_list': Section.objects.filter(page=page),
            'page': page,
            'page_number': page_number,
            'page_count': len(pages)
        }, context_instance=RequestContext(request))
    except Exception as e:
        print e.__str__()
        return HttpResponseBadRequest(render_to_response('400.html'))
    
def generate_hash(request, album_id, page_id):
    code = str(album_id) + "_" + str(page_id)
    if request != None:
        link = request.get_host() + '/link/?url='
    else:
        link = '/link/?url='
    link += base64.b64encode(code)
    return link
