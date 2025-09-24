from main.models import Enrollment, Badge, AwardedBadge
from django.db import models

def update_total_points(enrollment: Enrollment):
    total_points = (enrollment.point_entries.aggregate(total=models.Sum("reason__default_points"))["total"] or 0)

    enrollment.total_points = total_points
    enrollment.save(update_fields=["total_points"])


def update_ranks_for_course(course):
    enrollments = (
        Enrollment.objects.filter(group__course=course, is_active=True)
        .order_by("-total_points", "id")
    )

    for idx, enrollment in enumerate(enrollments, start=1):
        if enrollment.rank != idx:
            enrollment.rank = idx
            enrollment.save(update_fields=["rank"])


def check_and_award_badges(enrollment: Enrollment):
    badges = Badge.objects.filter(criteria__isnull=False)

    for badge in badges:
        if AwardedBadge.objects.filter(enrollment=enrollment, badge=badge).exists():
            continue

        award = True
        if badge.criteria:
            crit = badge.criteria
            if crit.type == "points" and enrollment.total_points < int(crit.value):
                award = False
            elif crit.type == "rank" and (
                enrollment.rank is None or enrollment.rank > int(crit.value)
            ):
                award = False

        if award:
            AwardedBadge.objects.create(enrollment=enrollment, badge=badge)