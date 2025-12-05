from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.post_list_api, name='api-post-list'),
    path('posts/<int:pk>/', views.post_detail_api, name='api-post-detail'),
    path('posts/create/', views.create_post_api, name='api-post-create'),
    path('posts/<int:pk>/update/', views.update_post_api, name='api-post-update'),
    path('posts/<int:pk>/delete/', views.delete_post_api, name='api-post-delete'),
    path('posts/<int:pk>/publish/', views.publish_post_api, name='api-post-publish'),
    path('posts/<int:pk>/comments/add/', views.add_comment_api, name='api-add-comment'),
    path('auth/session-login/', views.session_login_api, name='api-session-login'),
]
