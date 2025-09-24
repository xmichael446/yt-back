import nested_admin
from django.contrib import admin
from django.utils.html import format_html

from .admin_extras.inlines import GroupInline, BadgeCriteriaInline
from .models import (
    Course, Student, Enrollment,
    PointReason, PointEntry,
    Reward, RewardRedemption,
    BadgeCriteria, Badge, AwardedBadge
)


@admin.register(Course)
class CourseAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "created_at")
    inlines = [GroupInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(created_by=request.user)
        return user_qs

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "access_code", "created_by", "created_at")
    search_fields = ("first_name", "last_name", "access_code")
    readonly_fields = ("access_code", "created_by", "created_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(created_by=request.user)
        return user_qs

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "group", "total_points", "rank", "balance", "is_active")
    list_filter = ("group__course", "is_active")
    search_fields = ("student__first_name", "student__last_name", "group__name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(student__created_by=request.user)
        return user_qs


@admin.register(PointReason)
class PointReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "default_points", "default_coins")
    search_fields = ("name",)


@admin.register(PointEntry)
class PointEntryAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "reason__name",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(enrollment__student__created_by=request.user)
        return user_qs


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name", "cost", "course")
    search_fields = ("name", "course__name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(course__created_by=request.user)
        return user_qs


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "reward", "created_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(enrollment__student__created_by=request.user)
        return user_qs


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "preview_icon", "has_criteria", "created_at")
    search_fields = ("name",)
    inlines = [BadgeCriteriaInline]

    def preview_icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="height:30px;"/>', obj.icon.url)
        return "—"
    preview_icon.short_description = "Icon"

    def has_criteria(self, obj):
        return hasattr(obj, "criteria") and obj.criteria is not None
    has_criteria.boolean = True
    has_criteria.short_description = "Has Criteria?"

@admin.register(AwardedBadge)
class AwardedBadgeAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "badge", "created_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_qs = qs.filter(enrollment__student__created_by=request.user)
        return user_qs
