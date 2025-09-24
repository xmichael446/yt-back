import string
import random

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

def generate_access_code(prefix, length):
    digits = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}{digits}"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Course(TimestampedModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Group(TimestampedModel):
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="groups")
    access_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)

    def save(self, *args, **kwargs):
        if not self.access_code:
            code = generate_access_code("YT-G", 4)
            while Group.objects.filter(access_code=code).exists():
                code = generate_access_code()
            self.access_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.course})"


class Student(TimestampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    access_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.access_code:
            code = generate_access_code("YT-E", 6)
            while Student.objects.filter(access_code=code).exists():
                code = generate_access_code()
            self.access_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Enrollment(TimestampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="enrollments")
    total_points = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "group")

    def __str__(self):
        return f"{self.student} in {self.group}"


class PointReason(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    default_points = models.IntegerField(default=0)
    default_coins = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class PointEntry(TimestampedModel):
    reason = models.ForeignKey(PointReason, on_delete=models.SET_NULL, null=True, related_name="point_entries")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="point_entries")

    def __str__(self):
        return f"{self.enrollment} - {self.reason} ({self.reason.default_points})"


class Reward(TimestampedModel):
    name = models.CharField(max_length=255)
    cost = models.IntegerField()
    link = models.URLField(max_length=255, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="rewards")

    def __str__(self):
        return f"{self.name} ({self.course})"


class RewardRedemption(TimestampedModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="redemptions")
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name="redemptions")

    def __str__(self):
        return f"{self.enrollment} redeemed {self.reward}"


class BadgeCriteria(TimestampedModel):
    CRITERIA_TYPES = [
        ("points", "Points Threshold"),
        ("rank", "Rank Reached"),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=CRITERIA_TYPES)
    value = models.CharField(max_length=255)
    badge = models.OneToOneField(
        "Badge",
        on_delete=models.CASCADE,
        related_name="criteria",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} ({self.type}={self.value})"

class Badge(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True, null=True)
    icon = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class AwardedBadge(TimestampedModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="awarded_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")

    def __str__(self):
        return f"{self.enrollment} awarded {self.badge}"
