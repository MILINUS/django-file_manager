from io import BytesIO
import uuid
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobClient
from django.conf import settings
from PIL import Image, ImageDraw
from msrest.authentication import CognitiveServicesCredentials
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from . import models

cog_key = '2b45dd93ad3c49558d80a40df13b1c85'
cog_endpoint = 'https://server-computer-vision.cognitiveservices.azure.com/'
ALLOWED_EXTENTIONS = ['.jpg','.png','.jpeg','.JPG']
local_path='C:/Users/Mehdi/Desktop/test-django-azure/django-file_manager/files/static/image/'
def create_blob_client(file_name):

    default_credential = DefaultAzureCredential()

    secret_client = SecretClient(
        vault_url=settings.AZURE_VAULT_ACCOUNT, credential=default_credential
    )

    storage_credentials = secret_client.get_secret(name=settings.AZURE_STORAGE_KEY_NAME)

    return BlobClient(
        account_url=settings.AZURE_STORAGE_ACCOUNT,
        container_name=settings.AZURE_APP_BLOB_NAME,
        blob_name=file_name,
        credential=storage_credentials.value,
    )


def check_file_ext(path):
    ext = Path(path).suffix
    return ext in ALLOWED_EXTENTIONS


def download_blob(file):
    blob_client = create_blob_client(file)
    if not blob_client.exists():
        return
    blob_content = blob_client.download_blob()
    return blob_content
    

def save_file_url_to_db(file_url):
    new_file = models.File.objects.create(file_url=file_url)
    new_file.save()
    return new_file

def upload_file_to_blob(file):

    if not check_file_ext(file.name):
        return

    file_prefix = uuid.uuid4().hex
    ext = Path(file.name).suffix
    file_name = f"{file_prefix}{ext}"
    file_content = file.read()
    file_io = BytesIO(file_content)
    blob_client = create_blob_client(file_name=file_name)
    blob_client.upload_blob(data=file_io)
    # print(file_io.getvalue())
    file_object = save_file_url_to_db(blob_client.url)
    

    return file_object
def predict_and_upload_image(file):
    title=''
    url=file.file_url
    computervision_client = ComputerVisionClient(cog_endpoint,CognitiveServicesCredentials(cog_key))
    test=Image.open(BytesIO(requests.get(url).content))
    description = computervision_client.describe_image(url)
    for caption in description.captions:
        title = title + " '{}'\n(Confidence: {:.2f}%)".format(caption.text, caption.confidence * 100)
    plt.title(title)
    plt.axis('off')
    plt.imshow(test)
    plt.savefig(local_path+file.file_name)
    upload_file_path = local_path+file.file_name
    blob_client = create_blob_client(file)
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)
    url = blob_client.url
    return url