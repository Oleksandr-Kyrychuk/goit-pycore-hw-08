from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('author/<int:author_id>/', views.author_detail, name='author_detail'),
    path('add_author/', views.add_author, name='add_author'),
    path('add_quote/', views.add_quote, name='add_quote'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('tag/<str:tag_name>/', views.tag_quotes, name='tag_quotes'),
    path('scrape/', views.scrape_quotes, name='scrape'),  # Переконайтеся, що name='scrape'
]