from django.contrib import admin
from .models import User, BlacklistedToken

# Register your models here.
admin.site.register(SafetyReport)