from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    TechnicalResourceCategorySchema,
    TechnicalResource,
    UserTechnicalProfile,
    RecommendationHistorySchema
)


# Serializer for TechnicalResourceCategory
class TechnicalResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalResourceCategorySchema
        fields = ['id', 'resource_name', 'resource_description']


class TechnicalResourceSerializer(serializers.ModelSerializer):
    # Nested serialization for category
    category = TechnicalResourceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        # queryset=TechnicalResourceCategorySchema.objects.all(),
        source='category',
        write_only=True,
        allow_null=True
    )

    class Meta:
        model = TechnicalResource
        fields = [
            'id', 'resource_title', 'resource_url', 'resource_description',
            'category', 'category_id', 'tags', 'difficulty_level',
            'metadata', 'created_at', 'updated_at', 'is_active',
            'views_count', 'recommendation_score'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# Serializer for UserTechnicalProfile
class UserTechnicalProfileSerializer(serializers.ModelSerializer):
    # Nested serialization for user
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    # Nested serialization for preferred categories
    preferred_categories = TechnicalResourceCategorySerializer(many=True, read_only=True)
    preferred_category_ids = serializers.PrimaryKeyRelatedField(
        # queryset=TechnicalResourceCategorySchema.objects.all(),
        source='preferred_categories',
        many=True,
        write_only=True,
        required=False
    )

    # Nested serialization for completed resources
    completed_resources = TechnicalResourceSerializer(many=True, read_only=True)
    completed_resource_ids = serializers.PrimaryKeyRelatedField(
        queryset=TechnicalResource.objects.all(),
        source='completed_resources',
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = UserTechnicalProfile
        fields = [
            'id', 'user', 'user_id', 'interests', 'skill_levels',
            'preferred_categories', 'preferred_category_ids',
            'learning_path', 'completed_resources', 'completed_resource_ids',
            'last_updated', 'total_learning_hours'
        ]


class RecommendationHistorySerializer(serializers.ModelSerializer):
    # Nested serialization for user
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    # Nested serialization for technical resource
    technical_resource = TechnicalResourceSerializer(read_only=True)
    technical_resource_id = serializers.PrimaryKeyRelatedField(
        queryset=TechnicalResource.objects.all(),
        source='technical_resource',
        write_only=True
    )

    class Meta:
        model = RecommendationHistorySchema
        fields = [
            'id', 'user', 'user_id', 'technical_resource', 'technical_resource_id',
            'interaction_type', 'interaction_timestamp', 'additional_metadata'
        ]



