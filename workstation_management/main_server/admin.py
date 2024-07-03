from django.contrib import admin

from .models import User
# Register your models here.

admin.site.register(User)

admin.site.site_header = 'Workstation Management'
admin.site.site_title = 'Workstation Management'
admin.site.index_title = 'Workstation Management'