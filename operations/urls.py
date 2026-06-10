from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('records/<int:pk>/', views.record_detail_view, name='record_detail'),
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/records/', views.api_records, name='api_records'),
    path('api/anomalies/', views.api_anomalies, name='api_anomalies'),
    path('api/records/<int:pk>/', views.api_record_detail, name='api_record_detail'),
    path('api/explain/<int:pk>/', views.api_explain, name='api_explain'),
    path('api/predict/', views.api_predict, name='api_predict'),
]
