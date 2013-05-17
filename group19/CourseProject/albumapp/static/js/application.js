var flickrPictures = null;
var dbPictures = [];
var sectionUrls = [];
var sectionCaptions = [];
var sectionPriorities = [];
var sectionIds = [];
var left = 0;
var right = 12;
var amount = 12;
var searchLimit = 60;

var modifyUrl = function(url, newPostFix){
	var basicUrl = url.substring(0, url.length-6);
	/*console.log(url);
	console.log(url.charAt(url.length-6));
	console.log(newPostFix);*/
	if (url.charAt(url.length-6) != "_") {
		basicUrl = url.substring(0, url.length-4);
	}
	if (newPostFix != ""){
		basicUrl = basicUrl.concat("_").concat(newPostFix).concat(".jpg");
	} else {
		basicUrl = basicUrl.concat(".jpg");
	}	
	return basicUrl;
}

var populateTemplates = function(sectionPriorities, sectionUrls, sectionCaptions, sectionIds){
	$('li.img').each(function(){
		for (var i = 0; i < sectionPriorities.length; i++){
			if ($(this).data('priority') == sectionPriorities[i]){
				$(this).addClass('section');
				$(this).attr('data-section-id', sectionIds[i]);
				var elem = $(this).find('.img-wrapper');
				$(this).find('.caption input[type="text"]').val(sectionCaptions[i]);
				$(this).find('.caption').css('display', 'block');
				loadImage(modifyUrl(sectionUrls[i], $(this).data('size')), $(this), true);
				$('.show_page form').append('<input type="hidden" name="section_change_pk" data-section-id="'+$(this).data('section-id')+'" value="0">');
			}
		}
	});	
}

var insertPicturesToPage = function(elem, data, start, end) {
	left = start;
	right = end;
	elem.html('');
	
	for (var i=start; i < end; i++) {
		if (data[i] != undefined) {
			var url = modifyUrl(data[i], "q");
			var html = '<li class="img img-polaroid"><img src="' + url + '"></img></li>'; 
			$(html).appendTo(elem).draggable({
			   start: function( event, ui ) {window.dragUrl = $(this).find('img').attr('src');},
		       containment: 'document',
		       helper: 'clone',
		       opacity: 0.70,
		       zIndex:10000,
		       appendTo: "body"				
			});
		}
	}
}

var searchFlickr = function() {
	dataToSubmit = $('#flickr_search_form input:first').val();
	
	if (dataToSubmit == ""){
		$.pnotify({
			title: 'Empty search field',
		    text: 'Please enter a search term and try again.',
		    icon: 'icon-warning-sign',
		    type: 'error',
	        width: "50%",
	        delay: 5000,
	        before_open: function(pnotify) {
	            // Position this notice in the top center of the screen.
	            pnotify.css({
	                "top": 0,
	                "left": ($(window).width() / 2) - (pnotify.width() / 2)
	            })
            }    
		});
	} else {
		// clear old results
		$('#flickr_search_results .results').html('');
		$.getJSON('/pictures/search_flickr/', {'text': dataToSubmit}, function(response_data) {
			left = 0;
			right = 12;
			searchLimit = 60;
			flickrPictures = response_data
			if (response_data.length > 0){
				if (response_data.length < 60){
					searchLimit = response_data.length
				}
				insertPicturesToPage($('#flickr_search_results .results'), response_data, left, right);
			}
		});
	}
}

var addPictureToDb = function(url){
	var token = $('input[name="csrfmiddlewaretoken"]').val();
	var data = {'url': url, 'csrfmiddlewaretoken': token};
	$.post('/pictures/add_picture_url_to_database/', data).done(function(data){
		//console.log(data);
	});
}

var toggleTabs = function(elem){
	if ($(elem).hasClass('flickr_pictures') || $(elem).hasClass('search')){
		if ($('#database_pictures').css('display') == 'block'){
			$('#database_pictures').fadeOut('fast', function(){
				$('#flickr_search_results').fadeIn('fast');
			});
		}		
	} else {
		if ($('#flickr_search_results').css('display') == 'block'){
			$('#flickr_search_results').fadeOut('fast', function(){
				$('#database_pictures').fadeIn('fast');
			});
		}			
	}
};

var loadImage = function(modUrl, elem, isSection){
	var img = $("<img />").attr('src', modUrl)
	    .load(function() {
	        if (!this.complete || typeof this.naturalWidth == "undefined" || this.naturalWidth == 0) {
	            alert('broken image!');
	        } else {
	        	if (isSection == false){
		        	if ($('#database_pictures').css('display') == 'none'){
		        		addPictureToDb(modifyUrl(modUrl, "")); // already in db-pictures aren't tried to add to db
		        	}
        			elem.html('<div class="img-wrapper"></div><div class="caption" style="display:none;"><input type="text" name="section_caption" placeholder="Your Text Here"/>'+
        					'<input type="hidden" name="picture_pk" value="'+modifyUrl(window.dragUrl, "")+'"></div>');	        		
	        	}
	        	img.css('display', 'none');
	        	$('.container-fluid').css('cursor', 'default');
	            elem.find('.img-wrapper').html(img);
	            var margLeft = null;
	            var margTop = null;	                      
	            if (isSection == false){
		            img.fadeIn();
    	            margLeft = (elem.outerWidth() - img.outerWidth())/2
	            	margTop = (elem.find('.img-wrapper').outerHeight() - img.outerHeight())/2;
		            if (margLeft > 9){
		            	if (margLeft < 20){
		            		margLeft = margLeft/2;
		            	}
			            img.animate({
			            	'marginLeft': margLeft
			            }, 300);		            	
		            }
		            img.animate({
		            	'marginTop': margTop
		            }, 300, function(){
		            	elem.find('.caption').fadeIn();
		            });	            	
	            } else {
	            	img.css('display', 'block');
	            	margLeft = (elem.outerWidth() - img.outerWidth())/2
	            	margTop = (elem.find('.img-wrapper').outerHeight() - img.outerHeight())/2;	
	            	console.log(margTop);
	            	console.log(margLeft);
	            	if (margLeft < 10) {
	            		margLeft = 0;
	            	}
	            	img.css({
	            		'marginLeft': margLeft,
	            		'marginTop': margTop
	            	})
	            	elem.find('.img-wrapper').css('height', elem.find('.img-wrapper').height()-margTop);
	            }
	        }
	    });
}

$(document).ready(function() {
	
	$('.container-fluid').css('minHeight', $(window).height()-150); // FOOTER PUSH
	
	$(".templates li.img").droppable({
	      drop: function( event, ui ) {
	      	$('.container-fluid').css('cursor', 'wait');
	      	elem = $(this); 
	      	if (elem.hasClass('section')){
	      		$('.show_page form').append('<input type="hidden" name="section_pk" value="'+elem.data('section-id')+'">');
	      		elem.removeClass('section');
	      		var secId = elem.data('section-id');
	      		elem.attr('data-section-id', '');
				$('.show_page form input[name="section_change_pk"]').each(function(){
					if ($(this).data('section-id') == secId){
						$(this).val('0');
					}
				});		      		
	      	}
	      	size = $(this).data('size');
	      	priority = $(this).data('priority');
	      	modUrl = modifyUrl(window.dragUrl, size);
	      	loadImage(modUrl, elem, false);
	      }
	});
	
	$('#search_flickr a').click(function(event) {
		event.preventDefault();
	    searchFlickr();
		$('.flickr_pictures').trigger('click');
	});
	
	$('.db_pictures').click(function(event) {
		event.preventDefault();
		$('ul.nav.nav-tabs li').each(function(){
			$(this).removeClass('active');
		});
		$(this).toggleClass('active');
		toggleTabs(this);
	});
	
	$('.flickr_pictures').click(function(event) {
		event.preventDefault();
		$('ul.nav.nav-tabs li').each(function(){
			$(this).removeClass('active');
		});
		$(this).toggleClass('active');
		toggleTabs(this);
	});
	
	$('#database_pictures .left').click(function(event){
		event.preventDefault();
		if (left != 0){
			insertPicturesToPage($('#database_pictures .results'), dbPictures, left-amount, right-amount);			
		}
	});
	
	$('#database_pictures .right').click(function(event){
		event.preventDefault();
		if (right != 60){
			insertPicturesToPage($('#database_pictures .results'), dbPictures, left+amount, right+amount);
		}
	});
	
	$('#flickr_search_results .left').click(function(event){
		event.preventDefault();
		if (left != 0){
			insertPicturesToPage($('#flickr_search_results .results'), flickrPictures, left-amount, right-amount);
		}
	});
	
	$('#flickr_search_results .right').click(function(event){
		event.preventDefault();
		if (right < searchLimit-1){
			insertPicturesToPage($('#flickr_search_results .results'), flickrPictures, left+amount, right+amount);			
		}
	});
	
	$('.form-submit').click(function(){
		$(this).parent().submit();
	});
	
	$('.caption input[type="text"]').change(function(){
		secId = $(this).closest('li').data('section-id');
		$('.show_page form input[name="section_change_pk"]').each(function(){
			if ($(this).data('section-id') == secId){
				$(this).val(secId);
			}
		});	
	});

	$('input.input-medium.search-query').keypress(function(event){
		var keycode = (event.keyCode ? event.keyCode : event.which);
		if(keycode == '13'){
			event.preventDefault();
		    searchFlickr();
			$('.flickr_pictures').trigger('click');			
		}
	});

	$('.add_page.btn').tooltip({
		trigger: "hover",
		placement: "right"
	});
	
	$('.remove_page.btn').tooltip({
		trigger: "hover",
		placement: "top"
	});		
})

