from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

class Image(models.Model):
    image_title = models.CharField(max_length =60)
    image_name = models.CharField(max_length =60)
    image_caption = models.CharField(max_length =60)
    
   



    


