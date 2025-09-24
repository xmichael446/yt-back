import nested_admin
from django.contrib import admin
from django.utils.html import format_html

from .admin_extras.inlines import GroupInline
from .admin_extras.mixins import UserOwnedQuerysetMixin, AutoCreatedByMixin
from .models import (
    Course, Student, Enrollment,
    PointReason, PointEntry,
    Reward, RewardRedemption, ActivityEntry
)


@admin.register(Course)
class CourseAdmin(nested_admin.NestedModelAdmin, UserOwnedQuerysetMixin, AutoCreatedByMixin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "created_at")
    inlines = [GroupInline]

    def filter_for_user(self, qs, request):
        return qs.filter(created_by=request.user)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin, AutoCreatedByMixin):
    list_display = ("first_name", "last_name", "access_code", "created_by", "created_at")
    search_fields = ("first_name", "last_name", "access_code")
    readonly_fields = ("access_code", "created_by", "created_at")

    def filter_for_user(self, qs, request):
        return qs.filter


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin):
    list_display = ("student", "group", "total_points", "rank", "balance", "is_active")
    list_filter = ("group__course", "is_active")
    search_fields = ("student__first_name", "student__last_name", "group__name")

    def filter_for_user(self, qs, request):
        return qs.filter(student__created_by=request.user)


@admin.register(PointReason)
class PointReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "default_points", "default_coins")
    search_fields = ("name",)


@admin.register(PointEntry)
class PointEntryAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin):
    list_display = ("enrollment", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "reason__name",
    )

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin):
    list_display = ("name", "cost", "course")
    search_fields = ("name", "course__name")

    def filter_for_user(self, qs, request):
        return qs.filter(course__created_by=request.user)


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin):
    list_display = ("enrollment", "reward", "created_at")

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)


@admin.register(ActivityEntry)
class ActivityEntryAdmin(admin.ModelAdmin, UserOwnedQuerysetMixin):
    list_display = ("enrollment", "action", "points", "coins_change", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("enrollment__student__first_name", "enrollment__student__last_name")
    ordering = ("-created_at",)

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)
