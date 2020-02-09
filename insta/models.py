from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from tinymce.models import HTMLField



class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic = models.ImageField(blank=True,upload_to='prof_pics',default='default.png')
    bio = models.TextField(blank=True)
    followers= models.ManyToManyField(User,related_name='followers', blank=True)
    following= models.ManyToManyField(User,related_name='following', blank=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.user}'s Profile"

class Post(models.Model):
    image = models.ImageField( null=True,upload_to ='images/')
    name= models.CharField(max_length=120,blank=True,default='post')
    caption = HTMLField()
    created_date = models.DateTimeField(auto_now_add=True )
    likes = models.IntegerField(default=0)
    profile=models.ForeignKey(User,on_delete=models.CASCADE)
    objects = models.Manager()
     
    
    def __str__(self):
        auth = self.profile
        cap = self.caption
        
        eka = "User: '{}' Posted: {}".format(auth, cap)
        return eka

    def save_post(self):
        self.save()

    def delete_post(self):
        self.delete()

    def update_caption(self,new_cap):
        self.caption=new_cap
        self.save()

class Comment(models.Model):
    comment = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post,on_delete=models.CASCADE)
    objects = models.Manager()

    def __str__(self):
        return self.comment

