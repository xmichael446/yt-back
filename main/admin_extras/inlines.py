import nested_admin
from django.contrib import admin

from main.models import Enrollment, Group, BadgeCriteria


class EnrollmentInline(nested_admin.NestedTabularInline):
    model = Enrollment
    extra = 1
    readonly_fields = ("total_points", "rank", "balance")


class GroupInline(nested_admin.NestedStackedInline):
    model = Group
    extra = 1
    readonly_fields = ("access_code",)
    inlines = [EnrollmentInline]


class BadgeCriteriaInline(admin.StackedInline):
    model = BadgeCriteria
    extra = 0
    max_num = 1
    can_delete = True
    fk_name = "badge"