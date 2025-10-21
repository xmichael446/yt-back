import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PointEntry, ActivityEntry, Student, Enrollment, YTInstance
from .tasks import update_ranks_for_course_task, send_student_to_cd_mock


@receiver(post_save, sender=ActivityEntry)
def handle_activityentry_save(sender, instance, created, **kwargs):
    if not created:
        return

    enrollment = instance.enrollment
    course = enrollment.group.course
    update_ranks_for_course_task.delay(course.id)


@receiver(post_delete, sender=ActivityEntry)
def handle_activityentry_delete(sender, instance, **kwargs):
    enrollment = instance.enrollment
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


@receiver(post_save, sender=Enrollment)
def create_cd_mock_student(sender, instance, created, **kwargs):
    if not created:
        return

    send_student_to_cd_mock.delay(
        instance.student.access_code,
        instance.student.first_name,
        instance.student.last_name,
        instance.group.course.created_by.username
    )