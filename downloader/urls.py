from django.urls import path
from .views import VideoDownloadView, index

urlpatterns = [
    path('', index, name='index'),  # Frontend page
    path('download/', VideoDownloadView.as_view(), name='video_download'),  # API endpoint
]
