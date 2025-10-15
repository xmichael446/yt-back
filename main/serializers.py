# serializers.py
from rest_framework import serializers
from .models import Student, Group, Enrollment, Course, Reward, RewardRedemption, PointEntry, ActivityEntry


class EnrollmentCheckSerializer(serializers.Serializer):
    student_code = serializers.CharField()
    group_code = serializers.CharField()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]


class EnrollmentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["full_name", "total_points", "rank", "balance"]

    def get_full_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ["id", "name", "cost"]


class RewardRedemptionSerializer(serializers.ModelSerializer):
    reward = RewardSerializer(read_only=True)
    awarded = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = RewardRedemption
        fields = ["id", "reward", "awarded", "link"]

    def get_awarded(self, obj):
        return obj.created_at

    def get_link(self, obj):
        return obj.reward.link


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityEntry
        fields = ["action", "for_date", "points", "coins_change"]