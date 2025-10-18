import nested_admin
from django.contrib import admin
from django.db.models import Q

from .admin_extras.inlines import GroupInline, EnrollmentInline
from .admin_extras.mixins import UserOwnedQuerysetMixin, AutoCreatedByMixin
from .models import (
    Course, Student, Enrollment,
    PointReason, PointEntry,
    Reward, RewardRedemption, ActivityEntry, Group, YTInstance
)

admin.site.site_header = "YouTrack Administration"
admin.site.site_title = "YouTrack Admin"
admin.site.index_title = "Welcome to the YouTrack Admin"


@admin.register(YTInstance)
class YTInstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "admin", "get_coordinators", "get_point_reasons", "created_at", "updated_at")
    search_fields = ("name", "admin__username", "coordinators__username")
    autocomplete_fields = ("admin", "coordinators", "point_reasons")
    filter_horizontal = ("coordinators", "point_reasons")

    def get_coordinators(self, obj):
        return ", ".join([c.username for c in obj.coordinators.all()])
    get_coordinators.short_description = "Coordinators"

    def get_point_reasons(self, obj):
        return ", ".join([c.name for c in obj.point_reasons.all()])
    get_point_reasons.short_description = "Point Reasons"

    class Meta:
        verbose_name = "YouTrack Instance"
        verbose_name_plural = "YouTrack Instances"


@admin.register(Course)
class CourseAdmin(UserOwnedQuerysetMixin, AutoCreatedByMixin, nested_admin.NestedModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "created_at")
    inlines = [GroupInline]

    def filter_for_user(self, qs, request):
        return qs.filter(created_by=request.user)


@admin.register(Group)
class GroupAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("name", "access_code", "coordinator", "course",)
    readonly_fields = ("access_code",)
    inlines = [EnrollmentInline]

    def filter_for_user(self, qs, request):
        return qs.filter(Q(coordinator=request.user) | Q(course__created_by=request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = request.user

        if db_field.name == "course" and not user.is_superuser:
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(created_by=user)
        elif db_field.name == "coordinator":
            if user.is_superuser:
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(is_staff=True)
            else:
                try:
                    yt_instance = YTInstance.objects.get(admin=user)
                    kwargs["queryset"] = yt_instance.coordinators.all()
                except YTInstance.DoesNotExist:
                    kwargs["queryset"] = db_field.remote_field.model.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(Student)
class StudentAdmin(UserOwnedQuerysetMixin, AutoCreatedByMixin, admin.ModelAdmin):
    list_display = ("first_name", "last_name", "access_code", "created_by",)
    search_fields = ("first_name", "last_name", "access_code")
    readonly_fields = ("access_code", "created_by",)

    def filter_for_user(self, qs, request):
        user = request.user

        if user.is_superuser:
            return qs

        try:
            yt_instance = YTInstance.objects.get(admin=user)
            coordinator_ids = yt_instance.coordinators.values_list("id", flat=True)
            return qs.filter(Q(created_by=user) | Q(created_by__in=coordinator_ids))
        except YTInstance.DoesNotExist:
            pass

        try:
            yt_instance = YTInstance.objects.get(coordinators=user)
            return qs.filter(Q(created_by=user) | Q(created_by=yt_instance.admin))
        except YTInstance.DoesNotExist:
            pass

        return qs.filter(created_by=user)


@admin.register(Enrollment)
class EnrollmentAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("student", "group", "student_access_code", "total_points", "rank", "balance", "is_active")
    list_filter = ("group__course", "is_active")
    search_fields = ("student__first_name", "student__last_name", "group__name")

    def student_access_code(self, obj):
        if obj and obj.student:
            return obj.student.access_code
        return ""
    student_access_code.short_description = "Access Code"

    def filter_for_user(self, qs, request):
        return qs.filter(
            Q(student__created_by=request.user) |
            Q(group__coordinator=request.user)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = request.user

        if db_field.name == "student":
            if not user.is_superuser:
                kwargs["queryset"] = Student.objects.filter(created_by=user)

        elif db_field.name == "group":
            GroupModel = db_field.remote_field.model

            if user.is_superuser:
                kwargs["queryset"] = GroupModel.objects.all()

            else:
                try:
                    yt_instance = YTInstance.objects.get(admin=user)
                    kwargs["queryset"] = GroupModel.objects.filter(course__created_by=user)

                except YTInstance.DoesNotExist:
                    try:
                        yt_instance = YTInstance.objects.get(coordinators=user)
                        kwargs["queryset"] = GroupModel.objects.filter(coordinator=user)
                    except YTInstance.DoesNotExist:
                        kwargs["queryset"] = GroupModel.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PointReason)
class PointReasonAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("name", "default_points", "default_coins")
    search_fields = ("name", )

    def filter_for_user(self, qs, request):
        user = request.user

        try:
            yt_instance = YTInstance.objects.get(admin=user)
            return yt_instance.point_reasons
        except YTInstance.DoesNotExist:
            try:
                yt_instance = YTInstance.objects.get(coordinators=user)
                return yt_instance.point_reasons
            except YTInstance.DoesNotExist:
                return PointReason.objects.none()


@admin.register(PointEntry)
class PointEntryAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("enrollment", "reason", "for_date")
    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "enrollment__student__access_code",
        "reason__name",
    )
    date_hierarchy = "for_date"

    def filter_for_user(self, qs, request):
        return qs.filter(Q(enrollment__student__created_by=request.user) | Q(enrollment__group__coordinator=request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "enrollment":
                _Enrollment = self.model._meta.get_field("enrollment").remote_field.model

                kwargs["queryset"] = _Enrollment.objects.filter(group__coordinator=request.user)
            elif db_field.name == "reason":
                yt_instance = YTInstance.objects.get(coordinators=request.user)
                kwargs["queryset"] = yt_instance.point_reasons


        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Reward)
class RewardAdmin(UserOwnedQuerysetMixin, admin.ModelAdmin):
    list_display = ("name", "cost", "course")
    search_fields = ("name", "course__name")

    def filter_for_user(self, qs, request):
        return qs.filter(course__created_by=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            if not request.user.is_superuser:
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
    list_display = ("enrollment", "action", "points", "coins_change", "for_date")
    list_filter = ("action", "for_date")
    search_fields = ("enrollment__student__first_name", "enrollment__student__last_name")
    ordering = ("-for_date",)
    date_hierarchy = "for_date"

    def filter_for_user(self, qs, request):
        return qs.filter(Q(enrollment__student__created_by=request.user) | Q(enrollment__group__coordinator=request.user))
