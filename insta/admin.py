from django.contrib import admin
from .models import Post,UserProfile,Comment

class ProfileAdmin(admin.ModelAdmin):
    filter_horizontal=("followers","following")

# Register your models here.
admin.site.register(UserProfile,admin_class=ProfileAdmin)
admin.site.register(Post)
admin.site.register(Comment)
