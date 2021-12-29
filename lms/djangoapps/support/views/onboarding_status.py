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

        # make mutable
        request.GET = request.GET.copy()

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return JsonResponse([])

        request.GET['username'] = user.username
        enrollments = get_enrollments(user.username)

        # sort by enrollment date
        enrollments = sorted(enrollments, key = lambda x: x['created'], reverse=True)

        onboarding_status = {
            'verified_in': None,
            'current_status': None
        }

        for enrollment in enrollments:
            request.GET['course_id'] = enrollment['course_details']['course_id']

            # get status
            # TODO: Filter only verified tracks
            status = super().get(request).data

            if 'onboarding_status' in status:
                status['course_id'] = enrollment['course_details']['course_id']
                status['enrollment_date'] = enrollment['created']
                status['instructor_dashboard_link'] = '/courses/{}/instructor#view-special_exams'.format(status['course_id'])
                
                #  set most recent status
                if onboarding_status['current_status'] is None:
                    onboarding_status['current_status'] = status

                # Loop to find original verified course. Expensive!
                if status['onboarding_status'] == 'verified':
                    onboarding_status['verified_in'] = status
                    break         

        return JsonResponse(onboarding_status)