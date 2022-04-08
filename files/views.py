from hashlib import new
from pathlib import Path
import mimetypes
import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404, HttpResponse
from PIL import Image, ImageDraw
from .azure_file_controller import ALLOWED_EXTENTIONS, download_blob, upload_file_to_blob,create_blob_client,save_file_url_to_db
from io import BytesIO
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from . import models
from msrest.authentication import CognitiveServicesCredentials
import requests
import matplotlib.pyplot as plt
cog_key = '2b45dd93ad3c49558d80a40df13b1c85'
cog_endpoint = 'https://server-computer-vision.cognitiveservices.azure.com/'
local_path='./static/image/'
features = ['Description', 'Tags', 'Adult', 'Objects', 'Faces']
def index(request):
    return render(request, "files/index.html", {})
def upload_file2(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        ext = Path(file.name).suffix
        new_file = upload_file_to_blob(file)
        if not new_file:
            messages.warning(request, f"{ext} not allowed only accept {', '.join(ext for ext in ALLOWED_EXTENTIONS)} ")
            return render(request, "files/upload_file.html", {}) 
        
        new_file.file_name = file.name
        new_file.file_extention = ext
        messages.success(request, f"{file.name} was successfully uploaded")
        title=''
        fig=plt.figure(figsize=(10,10))
        a=fig.add_subplot(2,2,1)
        url=new_file.file_url
        computervision_client = ComputerVisionClient(cog_endpoint,CognitiveServicesCredentials(cog_key))
        test=Image.open(BytesIO(requests.get(url).content))
        analysis = computervision_client.analyze_image(url, visual_features=features)
        
        if (len(analysis.description.captions) == 0):
          title = 'No caption detected'
        else:
         for caption in analysis.description.captions:
            title = title + " '{}'\n(Confidence: {:.2f}%)".format(caption.text, caption.confidence * 100)
        #get objects
        if (len(analysis.objects) == 0):
          
            plt.xlabel('no objects detected')

        else:
        # Draw a rectangle around each object
         for object in analysis.objects:
            r = object.rectangle
            bounding_box = ((r.x, r.y), (r.x + r.w, r.y + r.h))
            draw = ImageDraw.Draw(test)
            draw.rectangle(bounding_box, outline='magenta', width=5)
            plt.annotate(object.object_property,(r.x, r.y), backgroundcolor='magenta')

    # Get faces
        if (len(analysis.faces) == 0):
         plt.ylabel('no faces detected')
        else: 
        # Draw a rectangle around each face
         for face in analysis.faces:
            r = face.face_rectangle
            bounding_box = ((r.left, r.top), (r.left + r.width, r.top + r.height))
            draw = ImageDraw.Draw(test)
            draw.rectangle(bounding_box, outline='lightgreen', width=5)
            annotation = 'Person aged approxilately {}'.format(face.age)
            plt.annotate(annotation,(r.left, r.top), backgroundcolor='lightgreen')
        plt.title(title)
        # plt.axis('off')
        plt.imshow(test)
        plt.savefig(local_path+new_file.file_name)
        upload_file_path = os.path.join(local_path,new_file.file_nameles)
        
        
        with open(upload_file_path, "rb") as data:
            blob_client = create_blob_client(str(file))
            blob_client.upload_blob(data)
            file_object = save_file_url_to_db(blob_client.url)
            file_object.save()
         
        return render(request, "files/upload_file.html", {}) 


    return render(request, "files/upload_file.html", {})
def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        ext = Path(file.name).suffix
        new_file = upload_file_to_blob(file)
        if not new_file:
            messages.warning(request, f"{ext} not allowed only accept {', '.join(ext for ext in ALLOWED_EXTENTIONS)} ")
            return render(request, "files/upload_file.html", {}) 
        
        new_file.file_name = file.name
        new_file.file_extention = ext
        messages.success(request, f"{file.name} was successfully uploaded")
        title=''
        url=new_file.file_url
        computervision_client = ComputerVisionClient(cog_endpoint,CognitiveServicesCredentials(cog_key))
        test=Image.open(BytesIO(requests.get(url).content))
        description = computervision_client.describe_image(url)
        for caption in description.captions:
            title = title + " '{}'\n(Confidence: {:.2f}%)".format(caption.text, caption.confidence * 100)
        plt.title(title)
        plt.axis('off')
        plt.imshow(test)
        plt.savefig(local_path+new_file.file_name)
        upload_file_path = local_path+new_file.file_name
        
        with open(upload_file_path, "rb") as data:
            blob_client = create_blob_client(str(file))
            blob_client.upload_blob(data)
            file_object = save_file_url_to_db(blob_client.url)
            file_object.save()
         
        return render(request, "files/upload_file.html", {}) 


    return render(request, "files/upload_file.html", {})

def list_files(request):
    files = models.File.objects.filter(deleted=0)
    context = {"files": files}
    return render(request, "files/list_files.html", context=context)
def list_images(request):
    files = models.File.objects.filter(deleted=0)
    context = {"files": files}
    for file in files:
        print(file.file_url)
    return render(request, "files/list_images.html", context=context)
def download_file(request, file_id):
    file = models.File.objects.get(pk=file_id)
    file_name = file.file_name
    file_type, _ = mimetypes.guess_type(file_name)
    url = file.file_url
    blob_name = url.split("/")[-1]
    blob_content = download_blob(blob_name)
    if blob_content:
        response = HttpResponse(blob_content.readall(), content_type=file_type)
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        messages.success(request, f"{file_name} was successfully downloaded")
        return response
    return Http404


def delete_file(request,file_id):
    file = models.File.objects.get(pk=file_id)
    file.deleted = 1
    file.save()
    return redirect("list_files")
def predict_image(request,file_id):
    file = models.File.objects.get(pk=file_id)
    title=''
    url=file.file_url
    computervision_client = ComputerVisionClient(cog_endpoint,CognitiveServicesCredentials(cog_key))
    test=Image.open(BytesIO(requests.get(url).content))
    description = computervision_client.describe_image(url)
    context = {"description": description,"file":file}
    for caption in description.captions:
        title = title + " '{}'\n(Confidence: {:.2f}%)".format(caption.text, caption.confidence * 100)
    plt.title(title)
    plt.axis('off')
    plt.imshow(test)
    plt.savefig('C:/Users/Mehdi/Desktop/test-django-azure/django-file_manager/files/static/'+file.file_name)
    return render(request, "files/predict_image.html",context=context)

def get_url(request,file_id):
    file = models.File.objects.get(pk=file_id)
    context={"file": file}
    return render(request, "files/predict_image.html",context=context)