# serializers.py
from rest_framework import serializers
from .models import Student, Group, Enrollment, Course, Reward, RewardRedemption, PointEntry


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

    class Meta:
        model = RewardRedemption
        fields = ["id", "reward", "awarded"]

    def get_awarded(self, obj):
        return obj.created_at


class ActivitySerializer(serializers.ModelSerializer):
    reason = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    coins = serializers.SerializerMethodField()

    class Meta:
        model = PointEntry
        fields = ["reason", "created_at", "points", "coins"]

    def get_reason(self, obj):
        return obj.reason.name

    def get_points(self, obj):
        return obj.reason.default_points

    def get_coins(self, obj):
        return obj.reason.default_coins