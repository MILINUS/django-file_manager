from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('upload_file/', views.upload_file2, name="upload_file"),
    path('list_files/', views.list_files, name="list_files"),
    path('list_images/', views.list_images, name="list_images"),
    path('download_file/<int:file_id>/', views.download_file, name="download_file"),
    path('delete_file/<int:file_id>/', views.delete_file, name="delete_file"),
    path('predict_image/<int:file_id>/', views.predict_image, name="predict_image"),
]