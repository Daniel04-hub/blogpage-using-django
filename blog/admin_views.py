from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.urls import path

def author_page(request):
    return HttpResponse("<h1>Author Page Inside Admin</h1>")

def user_page(request):
    return HttpResponse("<h1>User Management Page Inside Admin</h1>")
