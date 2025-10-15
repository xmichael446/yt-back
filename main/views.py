from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student, Group, Enrollment, Reward, RewardRedemption, PointEntry, ActivityEntry
from .serializers import EnrollmentCheckSerializer, GroupSerializer, \
    EnrollmentSerializer, RewardRedemptionSerializer, RewardSerializer, ActivitySerializer


class CheckEnrollmentView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EnrollmentCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_code = serializer.validated_data["student_code"]
        group_code = serializer.validated_data["group_code"]

        try:
            student = Student.objects.get(access_code=student_code)
        except Student.DoesNotExist:
            return Response(
                {"success": False, "message": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            group = Group.objects.get(access_code=group_code)
        except Group.DoesNotExist:
            return Response(
                {"success": False, "message": "Group not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = Enrollment.objects.get(
                student=student, group=group, is_active=True
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"success": False, "message": "You're not enrolled in this group"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"success": True, "message": "ok"},
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    def post(self, request, *args, **kwargs):
        student_code = request.data.get("student_code")
        group_code = request.data.get("group_code")

        if not student_code or not group_code:
            return Response(
                {"success": False, "message": "student_code and group_code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.get(access_code=student_code)
            group = Group.objects.select_related("course").get(access_code=group_code)
        except (Student.DoesNotExist, Group.DoesNotExist):
            return Response(
                {"success": False, "message": "Student or Group not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = Enrollment.objects.select_related("student", "group").get(
                student=student, group=group, is_active=True
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"success": False, "message": "Enrollment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        enrollment_data = EnrollmentSerializer(enrollment).data

        group_data = GroupSerializer(group).data
        group_enrollments = Enrollment.objects.filter(group=group, is_active=True).select_related("student").order_by(
            "rank")
        group_data["enrollments"] = EnrollmentSerializer(group_enrollments, many=True).data

        course = group.course
        course_data = {
            "name": course.name,
        }
        course_enrollments = (
            Enrollment.objects.filter(group__course=course, is_active=True)
            .select_related("student", "group")
            .order_by("rank")[:50]
        )
        course_data["enrollments"] = EnrollmentSerializer(course_enrollments, many=True).data

        return Response(
            {
                "success": True,
                "data": {
                    "enrollment": enrollment_data,
                    "group": group_data,
                    "course": course_data,
                },
            },
            status=status.HTTP_200_OK,
        )


class RewardListView(APIView):
    def post(self, request):
        student_code = request.data.get("student_code")
        group_code = request.data.get("group_code")

        if not student_code or not group_code:
            return Response(
                {"success": False, "message": "Missing student_code or group_code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = Student.objects.get(access_code=student_code)
        group = Group.objects.get(access_code=group_code)
        enrollment = get_object_or_404(
            Enrollment, student=student, group=group
        )

        all_rewards = Reward.objects.filter(course=enrollment.group.course)

        claimed_qs = RewardRedemption.objects.filter(enrollment=enrollment)
        claimed = RewardRedemptionSerializer(claimed_qs, many=True).data

        claimed_reward_ids = claimed_qs.values_list("reward_id", flat=True)
        available_qs = all_rewards.exclude(id__in=claimed_reward_ids).order_by("cost")
        available = RewardSerializer(available_qs, many=True).data

        return Response(
            {"success": True, "data": {"available": available, "claimed": claimed}}
        )


class RewardClaimView(APIView):
    def post(self, request):
        student_code = request.data.get("student_code")
        group_code = request.data.get("group_code")
        reward_id = request.data.get("reward_id")

        if not student_code or not group_code or not reward_id:
            return Response(
                {"success": False, "message": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = Student.objects.get(access_code=student_code)
        group = Group.objects.get(access_code=group_code)
        enrollment = get_object_or_404(
            Enrollment, student=student, group=group
        )
        reward = get_object_or_404(
            Reward, id=reward_id, course=enrollment.group.course
        )

        if RewardRedemption.objects.filter(enrollment=enrollment, reward=reward).exists():
            return Response(
                {"success": False, "message": "Reward already claimed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if enrollment.balance < reward.cost:
            return Response(
                {
                    "success": False,
                    "message": f"Reward costs {reward.cost} coins, you only have {enrollment.total_points}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ActivityEntry.objects.create(
            enrollment=enrollment,
            action=f'Claimed "{reward.name}"',
            points=0,
            coins_change=-reward.cost,
            for_date=timezone.now().date(),
        )

        redemption = RewardRedemption.objects.create(enrollment=enrollment, reward=reward)
        redemption_data = RewardRedemptionSerializer(redemption).data

        return Response(
            {
                "success": True,
                "data": redemption_data
            }
        )


class ActivitiesView(APIView):
    def post(self, request):
        student_code = request.data.get("student_code")
        group_code = request.data.get("group_code")

        if not student_code or not group_code:
            return Response(
                {"success": False, "message": "Missing student_code or group_code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = Student.objects.get(access_code=student_code)
        group = Group.objects.get(access_code=group_code)
        enrollment = get_object_or_404(
            Enrollment, student=student, group=group
        )

        activities_qs = enrollment.activities.order_by("-for_date")[:50]  # get latest 50
        activities = ActivitySerializer(activities_qs, many=True).data[::-1]  # reverse to oldest→newest

        return Response(
            {"success": True, "data": activities}
        )