import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PointEntry, Student
from .utils.signals import update_total_points, update_ranks_for_course, check_and_award_badges


@receiver(post_save, sender=PointEntry)
def handle_pointentry_save(sender, instance, **kwargs):
    enrollment = instance.enrollment
    update_total_points(enrollment)

    enrollment.balance += instance.reason.default_coins
    enrollment.save()

    course = enrollment.group.course
    update_ranks_for_course(course)

    check_and_award_badges(enrollment)


@receiver(post_delete, sender=PointEntry)
def handle_pointentry_delete(sender, instance, **kwargs):
    enrollment = instance.enrollment
    update_total_points(enrollment)

    enrollment.balance -= instance.reason.default_coins
    enrollment.save()

    course = enrollment.group.course
    update_ranks_for_course(course)

    check_and_award_badges(enrollment)


@receiver(post_save, sender=Student)
def create_cd_mock_student(sender, instance, created, **kwargs):
    if created:
        url = "http://localhost:8000/api/add_candidate/"

        payload = {
            "candidate_id": instance.access_code,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "created_by": instance.created_by.username,
        }

        try:
            res = requests.post(
                url,
                json=payload,
                timeout=5
            )
            res.raise_for_status()
        except Exception as e:
            print(f"Error sending to other server: {e}")
