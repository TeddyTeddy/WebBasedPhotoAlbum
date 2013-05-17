#!/usr/bin/python
# URL that generated this code:
# http://txt2re.com/index-python.php3?s=%3C?xml%20version=%221.0%22%20encoding=%22utf-8%22?%3E%3Cdjango-objects%20version=%221.0%22%3E%3Cobject%20pk=%22http://farm9.staticflickr.com/8432/7764493630_b854eee3e6.jpg%22%20model=%22albumapp.picture%22%3E%3C/object%3E%3C/django-objects%3E&-5&-6&-10

import re

txt='<?xml version="1.0" encoding="utf-8"?>\n<django-objects version="1.0"><object pk="http://farm9.staticflickr.com/8432/7764493630_b854eee3e6.jpg" model="albumapp.picture"></object></django-objects>'

re1='(<\\?xml version="1\\.0" encoding="utf-8"\\?>\n)'    # Tag 1
re2='(<django-objects version="1\\.0">)'    # Tag 2
re3='(.*?)'    # Non-greedy match on filler
re4='(<\\/django-objects>)'    # Tag 3

rg = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)
m = rg.search(txt)
if m:
    tag1=m.group(1)
    tag2=m.group(2)
    tag3=m.group(3)
    print "("+tag1+")"+"("+tag2+")"+"("+tag3+")"+"\n"