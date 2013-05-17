group19
=======

Our Project Plan is in our wiki:

https://studentwiki.aalto.fi/display/AnttiJoniHakan/Project+Plan

A copy of the project plan is also attached as PDF to the root.

Information
===========

Names and student-ids:
Joni Anttalainen 	79608V
Antti Ahonen		79109P
Hakan Cuzdan		xxxxxx 

What features you implemented and how much points you would like to give to yourself from those? Where do you feel that you were successful and where you had most problems.

We implemented Authentication with all requirements (200p). Basic album functionalities (500p). Public link to photo albums. Link can be recieved for each album. (100p). Share albums to Facebook (100p).
Integrate with an image service API. Users can search photos from flickr and add them to pages (100p). Use of Ajax (100p) (Flickr searching and picture adding to database, also section removal).
Hakan worked actively as our Project manager. 
We used Kanban to keep our project well managed. We had weekly Skype meetings. Our progress can be seen from kanban or Git. 
We also used both UI tests (These are registered in kanban user stories) and unit tests (albumapp.tests). Our django unit tests covered  71% of model code and 35% of view code,
we had more tests but had to comment them out because we didn't have time to fix them after minor architectural changes.
Our client side code passed HTML/CSS validators. We also used our groups aalto wiki page to share information. We would give ourselver 160p from non-functional 
requirements, because we couldn't achieve as good test coverage of view code as we planned. So we would give ourselves total 1260p.

We had problems to finish functionalities in time, because we wanted to test them enough and to make sure that each release works on heroku. We had a constant development rate, but
it was a bit too slow as we aimed for the highest grade. Therefore we were in a hurry in the last few days. We still achieved the level we aimed.

How you divided the work between the team members - who did what?

We all did many diffent types of tasks, but in the end Antti focused on developing client side code and styling of user interface.
Joni did both server and client side programming, but focused on the server side.
Hakan did programming too, but he worked as our Team manager and maintained our Kanban board and arranged Skype meetings etc.   

Our progress can be seen from Git and Kanban (Petri has been invited to our kanban board)

Running
=======

You can connect to our app with this link:

http://salty-caverns-9004.herokuapp.com/enter/

You can create a profile by givin a username and a password. Use of email is optional.
When you sign in you can create photo albums and edit them. Start by creating new from the sidebar. Edit the pages by clicking
the pages link in (amount of pages). Here you can see the page navigator and picture index / flickr search. Select the first page by
clicking its name, then choose one of the templates and after that drag & drop pictures from the sidebar. The pictures can be
ready database pictures or flickr search result pictures. Save the whole page from the bottom of the shown page.
