from main.models import Enrollment
from django.db import models

def update_coins_and_total_points(enrollment: Enrollment):
    total_points = (enrollment.activities.aggregate(total=models.Sum("points"))["total"] or 0)
    balance = (enrollment.activities.aggregate(total=models.Sum("coins_change"))["total"] or 0)

    enrollment.total_points = total_points
    enrollment.balance = balance
    enrollment.save(update_fields=["total_points", "balance"])


def update_ranks_for_course(course):
    enrollments = (
        Enrollment.objects.filter(group__course=course, is_active=True)
        .order_by("-total_points", "id")
    )

    for idx, enrollment in enumerate(enrollments, start=1):
        if enrollment.rank != idx:
            enrollment.rank = idx
            enrollment.save(update_fields=["rank"])
