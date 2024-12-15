import json
import numpy as np
import requests
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import ListView
from django.db import models

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from .models import *

from bs4 import BeautifulSoup
from celery import shared_task

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ResourceRecommendationStrategy:
    """Base class for recommendation strategies"""

    def get_recommendations(self, user_profile, n_recommendations: int = 10) -> List[models.Model]:
        raise NotImplementedError("Subclasses must implement recommendation logic")


class ContentBasedRecommendationStrategy(ResourceRecommendationStrategy):
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def get_recommendations(self, user_profile, n_recommendations: int = 10) -> List[models.Model]:
        # Existing content-based recommendation logic from previous implementation
        completed_resources = user_profile.completed_resources.all()

        if not completed_resources:
            return self._get_fallback_recommendations(n_recommendations)

        all_resources = TechnicalResource.objects.active()
        resource_contents = [
            f"{r.resource_title} {r.resource_description} {' '.join(r.tags or [])}"
            for r in all_resources
        ]

        tfidf_matrix = self.vectorizer.fit_transform(resource_contents)
        cosine_similarities = cosine_similarity(tfidf_matrix)

        similar_indices = set()
        for completed in completed_resources:
            resource_idx = list(all_resources).index(completed)
            similar_idx = np.argsort(cosine_similarities[resource_idx])[-n_recommendations:]
            similar_indices.update(similar_idx)

        recommended_resources = [
            all_resources[idx] for idx in similar_indices
            if all_resources[idx] not in completed_resources
        ]

        return recommended_resources[:n_recommendations]

    def _get_fallback_recommendations(self, n_recommendations: int) -> List[models.Model]:
        return list(TechnicalResource.objects.active().filter(
            difficulty_level='beginner'
        ).order_by('-recommendation_score')[:n_recommendations])


class CollaborativeRecommendationStrategy(ResourceRecommendationStrategy):
    def get_recommendations(self, user_profile, n_recommendations: int = 10) -> List[models.Model]:
        # Existing collaborative recommendation logic
        user_interests = set(user_profile.interests or [])

        similar_users = UserTechnicalProfile.objects.filter(
            interests__overlap=list(user_interests)
        ).exclude(
            user=user_profile.user
        )

        recommended_resources = TechnicalResource.objects.active().filter(
            completed_by_users__user__in=similar_users.values('user')
        ).exclude(
            completed_by_users__user=user_profile.user
        ).annotate(
            completion_count=Count('completed_by_users')
        ).filter(
            difficulty_level__in=self._get_appropriate_difficulty_levels(user_profile)
        ).order_by('-completion_count', '-recommendation_score')[:n_recommendations]

        return list(recommended_resources)

    def _get_appropriate_difficulty_levels(self, user_profile) -> List[str]:
        avg_skill_level = self._calculate_average_skill_level(user_profile)

        difficulty_mapping = {
            'none': ['beginner'],
            'beginner': ['beginner', 'intermediate'],
            'intermediate': ['intermediate', 'advanced'],
            'advanced': ['advanced', 'expert'],
            'expert': ['advanced', 'expert']
        }

        return difficulty_mapping.get(avg_skill_level, ['beginner', 'intermediate'])

    def _calculate_average_skill_level(self, user_profile) -> str:
        if not user_profile.skill_levels:
            return 'beginner'

        skill_level_mapping = {
            'none': 0,
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }

        skill_values = [
            skill_level_mapping[level]
            for level in user_profile.skill_levels.values()
        ]

        avg_level = sum(skill_values) / len(skill_values)
        reverse_mapping = {v: k for k, v in skill_level_mapping.items()}
        return reverse_mapping[round(avg_level)]


class ResourceRecommendationService:
    def __init__(self, user_profile):
        self.strategies = [
            ContentBasedRecommendationStrategy(),
            CollaborativeRecommendationStrategy()
        ]
        self.user_profile = user_profile

    def get_recommendations(self, n_recommendations: int = 10) -> List[models.Model]:
        """Get recommendations from multiple strategies"""
        recommendations = []
        for strategy in self.strategies:
            recommendations.extend(
                strategy.get_recommendations(self.user_profile, n_recommendations)
            )

        # Deduplicate and limit recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:n_recommendations]


class ResourceScraperService:
    DEFAULT_CATEGORIES = [
        'machine-learning',
        'cloud-computing',
        'devops',
        'backend-development'
    ]

    @classmethod
    def _map_category(cls, category: str) -> str:
        return {
            'machine-learning': 'ml',
            'cloud-computing': 'cloud',
            'devops': 'devops',
            'backend-development': 'backend'
        }.get(category, 'backend')

    @classmethod
    def web_scrape(cls, url, category):
        """Basic web scraping method"""
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        return {
            'title': soup.find('h1').text,
            'description': soup.find('div', class_='description').text,
            'category': cls._map_category(category)
        }

    @classmethod
    def selenium_scrape(cls, url):
        """Advanced scraping with Selenium for dynamic content"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        with webdriver.Chrome(options=options) as driver:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'tech-content'))
            )

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            return {
                'full_content': soup.find('div', class_='tech-content').text,
                'technologies': [
                    tech.text for tech in soup.find_all('span', class_='tech-tag')
                ],
                'difficulty_level': soup.find('div', class_='difficulty-rating')['data-level']
            }


@shared_task
def perform_scraping(categories=None):
    """Unified scraping task"""
    categories = categories or ResourceScraperService.DEFAULT_CATEGORIES
    results = []

    for category in categories:
        urls = [f'https://example.com/tech-resources/{category}']

        for url in urls:
            basic_data = ResourceScraperService.web_scrape(url, category)
            advanced_data = ResourceScraperService.selenium_scrape(url)

            combined_data = {**basic_data, **advanced_data}
            results.append(combined_data)

    # Save or process results
    with open('tech_resources.json', 'w') as f:
        json.dump(results, f)

    # Optional: Create or update TechnicalResource model instances
    for resource_data in results:
        TechnicalResource.objects.update_or_create(
            url=resource_data['url'],
            defaults={
                'title': resource_data.get('title'),
                'description': resource_data.get('description'),
                'category': resource_data.get('category'),
                'difficulty_level': resource_data.get('difficulty_level')
            }
        )

    return results


class RecommendedResourcesView(LoginRequiredMixin, ListView):
    template_name = 'resources/recommended_resources.html'
    context_object_name = 'recommended_resources'
    paginate_by = 10

    def get_queryset(self):
        user_profile, _ = UserTechnicalProfile.objects.get_or_create(user=self.request.user)
        recommendation_service = ResourceRecommendationService(user_profile)

        # Get recommendations
        recommendations = recommendation_service.get_recommendations(10)

        # Update recommendation scores
        self._update_recommendation_scores(recommendations)

        return recommendations

    def _update_recommendation_scores(self, resources):
        """Update recommendation scores based on user interactions"""
        for resource in resources:
            interaction_counts = RecommendationHistorySchema.objects.filter(
                technical_resource=resource
            ).values('interaction_type').annotate(
                count=Count('interaction_type')
            )

            weights = {
                'view': 1,
                'save': 2,
                'complete': 3,
                'skip': -1
            }

            score = sum(
                count['count'] * weights[count['interaction_type']]
                for count in interaction_counts
            )

            resource.recommendation_score = score
            resource.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Trigger new scraping if needed
        self._schedule_background_scraping()
        return context

    def _schedule_background_scraping(self):
        """Schedule background scraping for new resources"""
        user_profile = self.request.user.technical_profile
        categories = user_profile.preferred_categories.all()

        if categories.exists():
            category_names = [cat.resource_name for cat in categories]
            perform_scraping.delay(category_names)


