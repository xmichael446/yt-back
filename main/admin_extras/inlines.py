import nested_admin
from django.contrib import admin

from main.models import Enrollment, Group


class EnrollmentInline(nested_admin.NestedTabularInline):
    model = Enrollment
    extra = 1
    readonly_fields = ("total_points", "rank", "balance")


class GroupInline(nested_admin.NestedStackedInline):
    model = Group
    extra = 1
    readonly_fields = ("access_code",)
    inlines = [EnrollmentInline]
