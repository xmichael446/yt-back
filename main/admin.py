import nested_admin
from django.contrib import admin

from .admin_extras.inlines import GroupInline
from .admin_extras.mixins import UserOwnedQuerysetMixin, AutoCreatedByMixin
from .models import (
    Course, Student, Enrollment,
    PointReason, PointEntry,
    Reward, RewardRedemption, ActivityEntry
)


@admin.register(Course)
class CourseAdmin(UserOwnedQuerysetMixin, AutoCreatedByMixin, nested_admin.NestedModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "created_at")
    inlines = [GroupInline]

    def filter_for_user(self, qs, request):
        return qs.filter(created_by=request.user)


@admin.register(Student)
class StudentAdmin(UserOwnedQuerysetMixin, AutoCreatedByMixin, admin.ModelAdmin):
    list_display = ("first_name", "last_name", "access_code", "created_by", "created_at")
    search_fields = ("first_name", "last_name", "access_code")
    readonly_fields = ("access_code", "created_by", "created_at")

    def filter_for_user(self, qs, request):
        return qs.filter(created_by=request.user)


@admin.register(Enrollment)
class EnrollmentAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("student", "group", "total_points", "rank", "balance", "is_active")
    list_filter = ("group__course", "is_active")
    search_fields = ("student__first_name", "student__last_name", "group__name")

    def filter_for_user(self, qs, request):
        return qs.filter(student__created_by=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = Student.objects.filter(created_by=request.user)

        if db_field.name == "group":
            kwargs["queryset"] = (
                self.model._meta.get_field("group")
                .remote_field.model.objects.filter(course__created_by=request.user)
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PointReason)
class PointReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "default_points", "default_coins")
    search_fields = ("name",)


@admin.register(PointEntry)
class PointEntryAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("enrollment", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "reason__name",
    )

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "enrollment":
            kwargs["queryset"] = (
                self.model._meta.get_field("enrollment")
                .remote_field.model.objects.filter(student__created_by=request.user)
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Reward)
class RewardAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("name", "cost", "course")
    search_fields = ("name", "course__name")

    def filter_for_user(self, qs, request):
        return qs.filter(course__created_by=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs["queryset"] = (
                self.model._meta.get_field("course")
                .remote_field.model.objects.filter(created_by=request.user)
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("enrollment", "reward", "created_at")

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)


@admin.register(ActivityEntry)
class ActivityEntryAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("enrollment", "action", "points", "coins_change", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("enrollment__student__first_name", "enrollment__student__last_name")
    ordering = ("-created_at",)

    def filter_for_user(self, qs, request):
        return qs.filter(enrollment__student__created_by=request.user)
