import nested_admin
from django.contrib import admin

from main.models import Enrollment, Group, Student, YTInstance


class EnrollmentInline(nested_admin.NestedTabularInline):
    model = Enrollment
    extra = 1
    fields = ("student", "student_access_code", "group")  # show in this order
    readonly_fields = ("student_access_code", )

    def student_access_code(self, obj):
        if obj and obj.student:
            return obj.student.access_code
        return "-"
    student_access_code.short_description = "Access Code"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "student":
                kwargs["queryset"] = Student.objects.filter(created_by=request.user)
            elif db_field.name == "group":
                kwargs["queryset"] = Group.objects.filter(course__created_by=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GroupInline(nested_admin.NestedStackedInline):
    model = Group
    extra = 1
    readonly_fields = ("access_code",)
    inlines = [EnrollmentInline]

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
