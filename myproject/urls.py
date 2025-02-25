"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path
import myapp.views as myapp_views

urlpatterns = [
    path('admin/KvYyftgr2Ov9GjnMpoCG1i2EBWN/', myapp_views.admin),
    path('antired/KvYyftgr2Ov9GjnMpoCG1i2EBWN/', myapp_views.antired),
    path('admin-panel', admin.site.urls),
    path('teeeeeeeeeeeest/', myapp_views.test),
    path('<path:resource>', myapp_views.get_picture),
]
