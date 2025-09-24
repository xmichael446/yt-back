import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PointEntry, ActivityEntry
from .utils.signals import update_coins_and_total_points, update_ranks_for_course


@receiver(post_save, sender=ActivityEntry)
def handle_activityentry_save(sender, instance, created, **kwargs):
    if not created:
        return

    enrollment = instance.enrollment

    enrollment.total_points += instance.points
    enrollment.balance += instance.coins_change
    enrollment.save(update_fields=["total_points", "balance"])

    course = enrollment.group.course
    update_ranks_for_course(course)


@receiver(post_save, sender=PointEntry)
def handle_pointentry_save(sender, instance, created, **kwargs):
    if created:
        ActivityEntry.objects.create(
            enrollment=instance.enrollment,
            action=instance.reason.name.lower().capitalize(),
            points=instance.reason.default_points,
            coins_change=instance.reason.default_coins,
        )


# @receiver(post_save, sender=Student)
# def create_cd_mock_student(sender, instance, created, **kwargs):
#     if created:
#         url = "http://localhost:8000/api/add_candidate/"
#
#         payload = {
#             "candidate_id": instance.access_code,
#             "first_name": instance.first_name,
#             "last_name": instance.last_name,
#             "created_by": instance.created_by.username,
#         }
#
#         try:
#             res = requests.post(
#                 url,
#                 json=payload,
#                 timeout=5
#             )
#             res.raise_for_status()
#         except Exception as e:
#             print(f"Error sending to other server: {e}")
