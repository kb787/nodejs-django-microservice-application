from django.urls import path
from .views import (
    RecommendedResourcesView,
    ResourceScraperService,
    perform_scraping
)

urlpatterns = [
    path(
        'recommended-resources/',
        RecommendedResourcesView.as_view(),
        name='recommended_resources'
    ),
    path(
        'scrape-resources/',
        lambda request: perform_scraping(),
        name='scrape_resources'
    ),
]