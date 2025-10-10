import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PointEntry, ActivityEntry, Student
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


@receiver(post_save, sender=Student)
def create_cd_mock_student(sender, instance, created, **kwargs):
    if created:
        url = "https://cd-mock-api.xmichael446.com/api/add_candidate/"

        payload = {
            "candidate_id": instance.access_code,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "created_by": instance.created_by.username,
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": "QODIRALI_ABDUSAMATOV",
        }

        try:
            res = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=5,
            )
            res.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending to other server: {e}")

