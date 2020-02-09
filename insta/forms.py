from django import forms
from .models import Post,Comment,UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields=['profile_pic']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['caption','image']

class CommentForm(forms.ModelForm):
    class Meta:
        model= Comment
        fields=['comment']

      
        
