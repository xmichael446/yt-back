from django.urls import path
from .views import CheckEnrollmentView, DashboardView, RewardListView, RewardClaimView, ActivitiesView

urlpatterns = [
    path("login/", CheckEnrollmentView.as_view(), name="check-enrollment"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("rewards", RewardListView.as_view(), name="rewards-list"),
    path("rewards/claim", RewardClaimView.as_view(), name="rewards-claim"),
    path("activities", ActivitiesView.as_view(), name="activities"),
]
