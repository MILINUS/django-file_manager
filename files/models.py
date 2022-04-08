from django.db import models
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
class File(models.Model):
    
    date_created = models.DateTimeField(auto_now_add=True)
    file_url = models.URLField(null=True)
    file_name = models.CharField(max_length=200, null=True)
    file_extention = models.CharField(max_length=200, null=True)
    deleted = models.BooleanField(null=True, default=False)
    # file_description = ComputerVisionClient.describe_image(file_url)


# class Image(models.Model):
    
#     date_created = models.DateTimeField(auto_now_add=True)
#     file_url = models.URLField(null=True)
#     file_name = models.CharField(max_length=200, null=True)
#     file_extention = models.CharField(max_length=200, null=True)
#     deleted = models.BooleanField(null=True, default=False)
#     file_description= models.CharField(max_length=200, null=True)