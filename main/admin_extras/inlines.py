import nested_admin
from django.contrib import admin

from main.models import Enrollment, Group, Student


class EnrollmentInline(nested_admin.NestedTabularInline):
    model = Enrollment
    extra = 1
    readonly_fields = ("total_points", "rank", "balance")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "student":
                kwargs["queryset"] = Student.objects.filter(created_by=request.user)

            if db_field.name == "group":
                kwargs["queryset"] = Group.objects.filter(course__created_by=request.user)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GroupInline(nested_admin.NestedStackedInline):
    model = Group
    extra = 1
    readonly_fields = ("access_code",)
    inlines = [EnrollmentInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(created_by=request.user)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
