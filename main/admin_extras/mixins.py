class UserOwnedQuerysetMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return self.filter_for_user(qs, request)

    def filter_for_user(self, qs, request):
        return qs


class AutoCreatedByMixin:
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
