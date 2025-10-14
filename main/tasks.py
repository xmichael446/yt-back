import requests
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


@shared_task(bind=True, autoretry_for=(requests.RequestException,), retry_backoff=True, max_retries=3)
def send_student_to_cd_mock(self, access_code, first_name, last_name, created_by_username):
    url = "https://cd-mock-api.xmichael446.com/api/add_candidate/"

    payload = {
        "candidate_id": access_code,
        "first_name": first_name,
        "last_name": last_name,
        "created_by": created_by_username,
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "QODIRALI_ABDUSAMATOV",
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        res.raise_for_status()
        return {"status": "success", "response": res.text}
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}
