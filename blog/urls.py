from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.post_list_api, name='api-post-list'),
    path('posts/<int:pk>/', views.post_detail_api, name='api-post-detail'),
    path('posts/<int:pk>/comments/add/', views.add_comment_api, name='api-add-comment'),
    path('comments/<int:comment_id>/reply/', views.reply_comment_api, name='api-reply-comment'),
    path('auth/session-login/', views.session_login_api, name='api-session-login'),
]
