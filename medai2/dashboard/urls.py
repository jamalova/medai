from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('datasets/', views.datasets, name='datasets'),
    path('classifier/', views.classifier, name='classifier'),
    path('analytics/', views.analytics, name='analytics'),

    # Mavjud API
    path('api/logs/', views.api_logs, name='api_logs'),

    # Qidiruv tizimi API
    path('api/search/', views.api_search, name='api_search'),
    path('api/search/compare/', views.api_search_compare, name='api_search_compare'),
    path('api/tokenize/', views.api_tokenize, name='api_tokenize'),
    path('api/search/stats/', views.api_search_stats, name='api_search_stats'),
    path('api/tokens/', views.api_tokens, name='api_tokens'),
    path('api/inverted-index/', views.api_inverted_index, name='api_inverted_index'),
    path('api/slots/', views.api_slots, name='api_slots'),
]
