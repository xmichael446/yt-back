import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PointEntry, ActivityEntry, Student, Enrollment
from .tasks import update_ranks_for_course_task, send_student_to_cd_mock


@receiver(post_save, sender=ActivityEntry)
def handle_activityentry_save(sender, instance, created, **kwargs):
    if not created:
        return

    enrollment = instance.enrollment

    enrollment.total_points += instance.points
    enrollment.balance += instance.coins_change
    enrollment.save(update_fields=["total_points", "balance"])

    course = enrollment.group.course
    update_ranks_for_course_task.delay(course.id)


@receiver(post_delete, sender=ActivityEntry)
def handle_activityentry_delete(sender, instance, **kwargs):
    enrollment = instance.enrollment

    enrollment.total_points -= instance.points
    enrollment.balance -= instance.coins_change
    enrollment.save(update_fields=["total_points", "balance"])

    course = enrollment.group.course
    update_ranks_for_course_task.delay(course.id)


@receiver(post_save, sender=PointEntry)
def handle_pointentry_save(sender, instance, created, **kwargs):
    if created:
        ActivityEntry.objects.create(
            enrollment=instance.enrollment,
            action=instance.reason.name.lower().capitalize(),
            points=instance.reason.default_points,
            coins_change=instance.reason.default_coins,
            linked_point_entry=instance,
            for_date=instance.for_date
        )


# @receiver(post_save, sender=Student)
# def create_cd_mock_student(sender, instance, created, **kwargs):
#     if created:
#         send_student_to_cd_mock.delay(
#             instance.access_code,
#             instance.first_name,
#             instance.last_name,
#             instance.created_by.username)

