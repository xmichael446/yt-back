from celery import shared_task
from django.db import transaction
from .models import Enrollment, Course


@shared_task
def update_ranks_for_course_task(course_id):
    course = Course.objects.get(id=course_id)

    enrollments = list(
        Enrollment.objects
        .filter(group__course=course, is_active=True)
        .order_by("-total_points", "id")
    )

    # Prepare updated objects
    updated = []
    for idx, enrollment in enumerate(enrollments, start=1):
        if enrollment.rank != idx:
            enrollment.rank = idx
            updated.append(enrollment)

    if updated:
        with transaction.atomic():
            Enrollment.objects.bulk_update(updated, ["rank"])

    return f"Updated {len(updated)} enrollments for course {course.id}"
