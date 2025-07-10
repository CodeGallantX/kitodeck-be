from django.contrib import admin
from .models import User, BlacklistedToken

# Register your models here.
admin.site.register(User)
admin.site.register(BlacklistedToken)