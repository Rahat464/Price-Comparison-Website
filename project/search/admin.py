from django.contrib import admin
from .models import amazon, newegg, ebay

admin.site.register(amazon)
admin.site.register(ebay)
admin.site.register(newegg)
