"""
Views for SSO records.
"""

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Q
from django.utils.decorators import method_decorator

from openedx.core.djangoapps.enrollments.api import get_enrollments

from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.support.decorators import require_support_permission
from edx_proctoring.views import StudentOnboardingStatusView


class OnboardingView(StudentOnboardingStatusView):
    """
    Returns a list of Onbording records for a given user.
    """
    @method_decorator(require_support_permission)
    def get(self, request, username_or_email):  # lint-amnesty, pylint: disable=missing-function-docstring

        if not request.GET._mutable:
            self.request.GET._mutable = True

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return JsonResponse([])

        self.request.GET['username'] = user.username
        enrollments = get_enrollments(user.username)
        all_resp = []

        for enrollment in enrollments:
            self.request.GET['course_id'] = enrollment['course_details']['course_id']
            resp = super().get(request).data
            resp['course_id'] = enrollment['course_details']['course_id']
            all_resp.append(resp)

        return JsonResponse(all_resp)