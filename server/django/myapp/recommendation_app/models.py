from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator, MinLengthValidator
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class TechnicalResourceCategorySchema(models.Model):
    resource_name = models.TextField()
    resource_description = models.TextField()

    class Meta:
        verbose_name_plural = "Technical Resource Categories"
        ordering = ['resource_name']

    def __str__(self):
        return self.resource_name


class TechnicalResourceManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class TechnicalResource(models.Model):

    DIFFICULTY_LEVELS = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert'))
    ]

    resource_title = models.TextField(
        db_index=True,
        validators=[MinLengthValidator(5)]
    )

    resource_url = models.URLField(
        unique=True,
        validators=[URLValidator()],
        db_index=True
    )

    resource_description = models.TextField(
        blank=True,
        null=True
    )

    category = models.ForeignKey(
        TechnicalResourceCategorySchema,
        on_delete=models.SET_NULL,
        related_name='resources',
        null=True
    )

    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        null=True
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )

    metadata = HStoreField(
        blank=True,
        null=True,
        help_text=_("Additional structured metadata about the resource")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    views_count = models.PositiveIntegerField(default=0)
    recommendation_score = models.FloatField(default=0.0)
    objects = TechnicalResourceManager()

    class Meta:
        indexes = [
            models.Index(fields=['resource_title', 'category']),  # Changed 'title' to 'resource_title'
            GinIndex(fields=['tags']),
            models.Index(fields=['difficulty_level', 'recommendation_score'])
        ]
        ordering = ['-recommendation_score', '-created_at']
        verbose_name_plural = "Technical Resources"

    def __str__(self):
        return self.resource_title


class UserTechnicalProfile(models.Model):

    SKILL_LEVELS = [
        ('none', _('No Skill')),
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert'))
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='technical_profile'
    )

    interests = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        null=True
    )

    skill_levels = HStoreField(
        blank=True,
        null=True,
        help_text=_("Skill levels for different technologies")
    )

    preferred_categories = models.ManyToManyField(
        TechnicalResourceCategorySchema,
        related_name='user_preferences',
        blank=True
    )

    learning_path = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        null=True
    )

    completed_resources = models.ManyToManyField(
        TechnicalResource,
        related_name='completed_by_users',
        blank=True
    )

    last_updated = models.DateTimeField(auto_now=True)

    total_learning_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        indexes = [
            GinIndex(fields=['interests']),
            models.Index(fields=['total_learning_hours'])
        ]
        verbose_name_plural = "User Technical Profiles"

    def __str__(self):
        return self.user


class RecommendationHistorySchema(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_histories'
    )
    technical_resource = models.ForeignKey(
        TechnicalResource,
        on_delete=models.CASCADE,
        related_name='recommendation_interactions'
    )
    interaction_type = models.CharField(
        max_length=50,
        choices=[
            ('view', _('View')),
            ('save', _('Save')),
            ('complete', _('Complete')),
            ('skip', _('Skip'))
        ]
    )

    interaction_timestamp = models.DateTimeField(auto_now_add=True)

    additional_metadata = HStoreField(
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('user', 'technical_resource', 'interaction_type')
        indexes = [
            models.Index(fields=['interaction_type', 'interaction_timestamp']),
        ]
        verbose_name_plural = "Recommendation Interactions"

    def __str__(self):
        return self.technical_resource




