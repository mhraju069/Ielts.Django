from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin

# Register your models here.

admin.site.register(Blog,ModelAdmin)
admin.site.register(Results,ModelAdmin)