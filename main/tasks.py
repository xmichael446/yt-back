import requests
from celery import shared_task
from django.db import transaction
from django.db.models import Sum

from .models import Enrollment, Course, ActivityEntry


@shared_task
def update_ranks_for_course_task(course_id):
    course = Course.objects.get(id=course_id)

    aggs = (
        ActivityEntry.objects
        .filter(enrollment__group__course=course, enrollment__is_active=True)
        .values("enrollment_id")
        .annotate(points_sum=Sum("points"), coins_sum=Sum("coins_change"))
    )

    sums_by_enrollment = {
        a["enrollment_id"]: (a["points_sum"] or 0, a["coins_sum"] or 0) for a in aggs
    }

    enrollments_qs = Enrollment.objects.filter(group__course=course, is_active=True)
    enrollments = list(enrollments_qs)

    to_update_totals = []
    for e in enrollments:
        pts, coins = sums_by_enrollment.get(e.id, (0, 0))
        if e.total_points != pts or e.balance != coins:
            e.total_points = pts
            e.balance = coins
            to_update_totals.append(e)

    if to_update_totals:
        with transaction.atomic():
            Enrollment.objects.bulk_update(to_update_totals, ["total_points", "balance"])

    enrollments_sorted = sorted(enrollments, key=lambda x: (-x.total_points, x.id))
    to_update_ranks = []
    for idx, e in enumerate(enrollments_sorted, start=1):
        if e.rank != idx:
            e.rank = idx
            to_update_ranks.append(e)

    if to_update_ranks:
        with transaction.atomic():
            Enrollment.objects.bulk_update(to_update_ranks, ["rank"])

    return (
        f"Updated totals/balances for {len(to_update_totals)} enrollments and "
        f"ranks for {len(to_update_ranks)} enrollments in course {course.id}"
    )

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
