from django.contrib import admin
from .models import Workstation, Engine, Host, ProxyMapping, Reservation, Tag, Template, EngineType


class EngineAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Workstation)
admin.site.register(Engine, EngineAdmin)
admin.site.register(Host)
admin.site.register(ProxyMapping)
admin.site.register(Reservation)
admin.site.register(Tag)
admin.site.register(Template)
admin.site.register(EngineType)
