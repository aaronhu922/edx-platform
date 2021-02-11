"""
Student Views
"""

import datetime
import logging
import uuid
from collections import namedtuple

import six
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sites.models import Site
from django.core.validators import ValidationError, validate_email
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_django_utils import monitoring as monitoring_utils
from eventtracking import tracker
from ipware.ip import get_ip
# Note that this lives in LMS, so this dependency should be refactored.
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from six import text_type

import track.views
from bulk_email.models import Optout
from course_modes.models import CourseMode

from pdfexam.models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem
from pdfexam.map_table_tmplate import domain_full_name_list, domain_start_name_list

from common.djangoapps.student.serializers import StudentSerializer

from lms.djangoapps.courseware.courses import get_courses, sort_by_announcement, sort_by_start_date
from edxmako.shortcuts import marketing_link, render_to_response, render_to_string
from entitlements.models import CourseEntitlement
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.catalog.utils import get_programs_with_type
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, CourseOverviewExtendInfo
from openedx.core.djangoapps.embargo import api as embargo_api
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming import helpers as theming_helpers
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangolib.markup import HTML, Text
from student.helpers import DISABLE_UNENROLL_CERT_STATES, cert_info, generate_activation_email_context, \
    do_create_account_no_registration
from student.message_types import AccountActivation, EmailChange, EmailChangeConfirmation, RecoveryEmailCreate
from student.models import (
    AccountRecovery,
    CourseEnrollment,
    PendingEmailChange,
    PendingSecondaryEmailChange,
    Registration,
    RegistrationCookieConfiguration,
    UserAttribute,
    UserProfile,
    UserSignupSource,
    UserStanding,
    create_comments_service_user,
    email_exists_or_retired,
    CourseEnrollmentInfo,
    CustomerService,
    get_user,
    CourseEnrollmentException
)
from student.signals import REFUND_ORDER
from student.tasks import send_activation_email
from student.text_me_the_app import TextMeTheAppFragmentView
from util.db import outer_atomic
from xmodule.modulestore.django import modulestore

from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from student.serializers import CourseEnrollmentInfoSerializer, CustomerServiceSerializer, CourseOverviewSerializer, \
    CourseOverviewExtendInfoSerializer

log = logging.getLogger("edx.student")

AUDIT_LOG = logging.getLogger("audit")
ReverifyInfo = namedtuple(
    'ReverifyInfo',
    'course_id course_name course_number date status display'
)
SETTING_CHANGE_INITIATED = 'edx.user.settings.change_initiated'
# Used as the name of the user attribute for tracking affiliate registrations
REGISTRATION_AFFILIATE_ID = 'registration_affiliate_id'
REGISTRATION_UTM_PARAMETERS = {
    'utm_source': 'registration_utm_source',
    'utm_medium': 'registration_utm_medium',
    'utm_campaign': 'registration_utm_campaign',
    'utm_term': 'registration_utm_term',
    'utm_content': 'registration_utm_content',
}
REGISTRATION_UTM_CREATED_AT = 'registration_utm_created_at'


def csrf_token(context):
    """
    A csrf token that can be included in a form.
    """
    token = context.get('csrf_token', '')
    if token == 'NOTPROVIDED':
        return ''
    return (HTML(u'<div style="display:none"><input type="hidden"'
                 ' name="csrfmiddlewaretoken" value="{}" /></div>').format(Text(token)))


# NOTE: This view is not linked to directly--it is called from
# branding/views.py:index(), which is cached for anonymous users.
# This means that it should always return the same thing for anon
# users. (in particular, no switching based on query params allowed)
def index(request, extra_context=None, user=AnonymousUser()):
    """
    Render the edX main page.

    extra_context is used to allow immediate display of certain modal windows, eg signup.
    """
    if extra_context is None:
        extra_context = {}

    courses = get_courses(user)

    if configuration_helpers.get_value(
        "ENABLE_COURSE_SORTING_BY_START_DATE",
        settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"],
    ):
        courses = sort_by_start_date(courses)
    else:
        courses = sort_by_announcement(courses)

    context = {'courses': courses}

    context['homepage_overlay_html'] = configuration_helpers.get_value('homepage_overlay_html')

    # This appears to be an unused context parameter, at least for the master templates...
    context['show_partners'] = configuration_helpers.get_value('show_partners', True)

    # TO DISPLAY A YOUTUBE WELCOME VIDEO
    # 1) Change False to True
    context['show_homepage_promo_video'] = configuration_helpers.get_value('show_homepage_promo_video', False)

    # Maximum number of courses to display on the homepage.
    context['homepage_course_max'] = configuration_helpers.get_value(
        'HOMEPAGE_COURSE_MAX', settings.HOMEPAGE_COURSE_MAX
    )

    # 2) Add your video's YouTube ID (11 chars, eg "123456789xX"), or specify via site configuration
    # Note: This value should be moved into a configuration setting and plumbed-through to the
    # context via the site configuration workflow, versus living here
    youtube_video_id = configuration_helpers.get_value('homepage_promo_video_youtube_id', "your-youtube-id")
    context['homepage_promo_video_youtube_id'] = youtube_video_id

    # allow for theme override of the courses list
    context['courses_list'] = theming_helpers.get_template_path('courses_list.html')

    # Insert additional context for use in the template
    context.update(extra_context)

    # Add marketable programs to the context.
    context['programs_list'] = get_programs_with_type(request.site, include_hidden=False)

    return render_to_response('index.html', context)


def compose_activation_email(root_url, user, user_registration=None, route_enabled=False, profile_name=''):
    """
    Construct all the required params for the activation email
    through celery task
    """
    if user_registration is None:
        user_registration = Registration.objects.get(user=user)

    message_context = generate_activation_email_context(user, user_registration)
    message_context.update({
        'confirm_activation_link': '{root_url}/activate/{activation_key}'.format(
            root_url=root_url,
            activation_key=message_context['key']
        ),
        'route_enabled': route_enabled,
        'routed_user': user.username,
        'routed_user_email': user.email,
        'routed_profile_name': profile_name,
    })

    if route_enabled:
        dest_addr = settings.FEATURES['REROUTE_ACTIVATION_EMAIL']
    else:
        dest_addr = user.email

    msg = AccountActivation().personalize(
        recipient=Recipient(user.username, dest_addr),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=message_context,
    )

    return msg


def compose_and_send_activation_email(user, profile, user_registration=None):
    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        profile: profile object of the current logged-in user
        user_registration: registration of the current logged-in user
    """
    route_enabled = settings.FEATURES.get('REROUTE_ACTIVATION_EMAIL')

    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    msg = compose_activation_email(root_url, user, user_registration, route_enabled, profile.name)

    send_activation_email.delay(str(msg))


@login_required
def course_run_refund_status(request, course_id):
    """
    Get Refundable status for a course.

    Arguments:
        request: The request object.
        course_id (str): The unique identifier for the course.

    Returns:
        Json response.

    """

    try:
        course_key = CourseKey.from_string(course_id)
        course_enrollment = CourseEnrollment.get_enrollment(request.user, course_key)

    except InvalidKeyError:
        logging.exception("The course key used to get refund status caused InvalidKeyError during look up.")

        return JsonResponse({'course_refundable_status': ''}, status=406)

    refundable_status = course_enrollment.refundable()
    logging.info("Course refund status for course {0} is {1}".format(course_id, refundable_status))

    return JsonResponse({'course_refundable_status': refundable_status}, status=200)


def _update_email_opt_in(request, org):
    """
    Helper function used to hit the profile API if email opt-in is enabled.
    """

    email_opt_in = request.POST.get('email_opt_in')
    if email_opt_in is not None:
        email_opt_in_boolean = email_opt_in == 'true'
        preferences_api.update_email_opt_in(request.user, org, email_opt_in_boolean)


@transaction.non_atomic_requests
@require_POST
@outer_atomic(read_committed=True)
def change_enrollment(request, check_access=True):
    """
    Modify the enrollment status for the logged-in user.

    TODO: This is lms specific and does not belong in common code.

    The request parameter must be a POST request (other methods return 405)
    that specifies course_id and enrollment_action parameters. If course_id or
    enrollment_action is not specified, if course_id is not valid, if
    enrollment_action is something other than "enroll" or "unenroll", if
    enrollment_action is "enroll" and enrollment is closed for the course, or
    if enrollment_action is "unenroll" and the user is not enrolled in the
    course, a 400 error will be returned. If the user is not logged in, 403
    will be returned; it is important that only this case return 403 so the
    front end can redirect the user to a registration or login page when this
    happens. This function should only be called from an AJAX request, so
    the error messages in the responses should never actually be user-visible.

    Args:
        request (`Request`): The Django request object

    Keyword Args:
        check_access (boolean): If True, we check that an accessible course actually
            exists for the given course_key before we enroll the student.
            The default is set to False to avoid breaking legacy code or
            code with non-standard flows (ex. beta tester invitations), but
            for any standard enrollment flow you probably want this to be True.

    Returns:
        Response

    """
    # Get the user
    user = request.user

    # Ensure the user is authenticated
    if not user.is_authenticated:
        return HttpResponseForbidden()

    # Ensure we received a course_id
    action = request.POST.get("enrollment_action")
    if 'course_id' not in request.POST:
        return HttpResponseBadRequest(_("Course id not specified"))

    try:
        course_id = CourseKey.from_string(request.POST.get("course_id"))
    except InvalidKeyError:
        log.warning(
            u"User %s tried to %s with invalid course id: %s",
            user.username,
            action,
            request.POST.get("course_id"),
        )
        return HttpResponseBadRequest(_("Invalid course id"))

    # Allow us to monitor performance of this transaction on a per-course basis since we often roll-out features
    # on a per-course basis.
    monitoring_utils.set_custom_attribute('course_id', text_type(course_id))

    if action == "enroll":
        # Make sure the course exists
        # We don't do this check on unenroll, or a bad course id can't be unenrolled from
        if not modulestore().has_course(course_id):
            log.warning(
                u"User %s tried to enroll in non-existent course %s",
                user.username,
                course_id
            )
            return HttpResponseBadRequest(_("Course id is invalid"))

        # Record the user's email opt-in preference
        if settings.FEATURES.get('ENABLE_MKTG_EMAIL_OPT_IN'):
            _update_email_opt_in(request, course_id.org)

        available_modes = CourseMode.modes_for_course_dict(course_id)

        # Check whether the user is blocked from enrolling in this course
        # This can occur if the user's IP is on a global blacklist
        # or if the user is enrolling in a country in which the course
        # is not available.
        redirect_url = embargo_api.redirect_if_blocked(
            course_id, user=user, ip_address=get_ip(request),
            url=request.path
        )
        if redirect_url:
            return HttpResponse(redirect_url)

        if CourseEntitlement.check_for_existing_entitlement_and_enroll(user=user, course_run_key=course_id):
            return HttpResponse(reverse('courseware', args=[six.text_type(course_id)]))

        # Check that auto enrollment is allowed for this course
        # (= the course is NOT behind a paywall)
        if CourseMode.can_auto_enroll(course_id):
            # Enroll the user using the default mode (audit)
            # We're assuming that users of the course enrollment table
            # will NOT try to look up the course enrollment model
            # by its slug.  If they do, it's possible (based on the state of the database)
            # for no such model to exist, even though we've set the enrollment type
            # to "audit".
            try:
                enroll_mode = CourseMode.auto_enroll_mode(course_id, available_modes)
                if enroll_mode:
                    CourseEnrollment.enroll(user, course_id, check_access=check_access, mode=enroll_mode)
            except Exception:  # pylint: disable=broad-except
                return HttpResponseBadRequest(_("Could not enroll"))

        # If we have more than one course mode or professional ed is enabled,
        # then send the user to the choose your track page.
        # (In the case of no-id-professional/professional ed, this will redirect to a page that
        # funnels users directly into the verification / payment flow)
        if CourseMode.has_verified_mode(available_modes) or CourseMode.has_professional_mode(available_modes):
            return HttpResponse(
                reverse("course_modes_choose", kwargs={'course_id': text_type(course_id)})
            )

        # Otherwise, there is only one mode available (the default)
        return HttpResponse()
    elif action == "unenroll":
        enrollment = CourseEnrollment.get_enrollment(user, course_id)
        if not enrollment:
            return HttpResponseBadRequest(_("You are not enrolled in this course"))

        certificate_info = cert_info(user, enrollment.course_overview)
        if certificate_info.get('status') in DISABLE_UNENROLL_CERT_STATES:
            return HttpResponseBadRequest(_("Your certificate prevents you from unenrolling from this course"))

        CourseEnrollment.unenroll(user, course_id)
        REFUND_ORDER.send(sender=None, course_enrollment=enrollment)
        return HttpResponse()
    else:
        return HttpResponseBadRequest(_("Enrollment action is invalid"))


@require_GET
@login_required
@ensure_csrf_cookie
def manage_user_standing(request):
    """
    Renders the view used to manage user standing. Also displays a table
    of user accounts that have been disabled and who disabled them.
    """
    if not request.user.is_staff:
        raise Http404
    all_disabled_accounts = UserStanding.objects.filter(
        account_status=UserStanding.ACCOUNT_DISABLED
    )

    all_disabled_users = [standing.user for standing in all_disabled_accounts]

    headers = ['username', 'account_changed_by']
    rows = []
    for user in all_disabled_users:
        row = [user.username, user.standing.changed_by]
        rows.append(row)

    context = {'headers': headers, 'rows': rows}

    return render_to_response("manage_user_standing.html", context)


@require_POST
@login_required
@ensure_csrf_cookie
def disable_account_ajax(request):
    """
    Ajax call to change user standing. Endpoint of the form
    in manage_user_standing.html
    """
    if not request.user.is_staff:
        raise Http404
    username = request.POST.get('username')
    context = {}
    if username is None or username.strip() == '':
        context['message'] = _('Please enter a username')
        return JsonResponse(context, status=400)

    account_action = request.POST.get('account_action')
    if account_action is None:
        context['message'] = _('Please choose an option')
        return JsonResponse(context, status=400)

    username = username.strip()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        context['message'] = _("User with username {} does not exist").format(username)
        return JsonResponse(context, status=400)
    else:
        user_account, _success = UserStanding.objects.get_or_create(
            user=user, defaults={'changed_by': request.user},
        )
        if account_action == 'disable':
            user_account.account_status = UserStanding.ACCOUNT_DISABLED
            context['message'] = _("Successfully disabled {}'s account").format(username)
            log.info(u"%s disabled %s's account", request.user, username)
        elif account_action == 'reenable':
            user_account.account_status = UserStanding.ACCOUNT_ENABLED
            context['message'] = _("Successfully reenabled {}'s account").format(username)
            log.info(u"%s reenabled %s's account", request.user, username)
        else:
            context['message'] = _("Unexpected account status")
            return JsonResponse(context, status=400)
        user_account.changed_by = request.user
        user_account.standing_last_changed_at = datetime.datetime.now(UTC)
        user_account.save()

    return JsonResponse(context)


@receiver(post_save, sender=User)
def user_signup_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handler that saves the user Signup Source when the user is created
    """
    if 'created' in kwargs and kwargs['created']:
        site = configuration_helpers.get_value('SITE_NAME')
        if site:
            user_signup_source = UserSignupSource(user=kwargs['instance'], site=site)
            user_signup_source.save()
            log.info(u'user {} originated from a white labeled "Microsite"'.format(kwargs['instance'].id))


@ensure_csrf_cookie
def activate_account(request, key):
    """
    When link in activation e-mail is clicked
    """
    # If request is in Studio call the appropriate view
    if theming_helpers.get_project_root_name().lower() == u'cms':
        monitoring_utils.set_custom_attribute('student_activate_account', 'cms')
        return activate_account_studio(request, key)

    # TODO: Use custom attribute to determine if there are any `activate_account` calls for cms in Production.
    # If not, the templates wouldn't be needed for cms, but we still need a way to activate for cms tests.
    monitoring_utils.set_custom_attribute('student_activate_account', 'lms')
    try:
        registration = Registration.objects.get(activation_key=key)
    except (Registration.DoesNotExist, Registration.MultipleObjectsReturned):
        messages.error(
            request,
            HTML(_(
                '{html_start}Your account could not be activated{html_end}'
                'Something went wrong, please <a href="{support_url}">contact support</a> to resolve this issue.'
            )).format(
                support_url=configuration_helpers.get_value(
                    'ACTIVATION_EMAIL_SUPPORT_LINK', settings.ACTIVATION_EMAIL_SUPPORT_LINK
                ) or settings.SUPPORT_SITE_LINK,
                html_start=HTML('<p class="message-title">'),
                html_end=HTML('</p>'),
            ),
            extra_tags='account-activation aa-icon'
        )
    else:
        if registration.user.is_active:
            messages.info(
                request,
                HTML(_('{html_start}This account has already been activated.{html_end}')).format(
                    html_start=HTML('<p class="message-title">'),
                    html_end=HTML('</p>'),
                ),
                extra_tags='account-activation aa-icon',
            )
        else:
            registration.activate()
            # Success message for logged in users.
            message = _('{html_start}Success{html_end} You have activated your account.')

            if not request.user.is_authenticated:
                # Success message for logged out users
                message = _(
                    '{html_start}Success! You have activated your account.{html_end}'
                    'You will now receive email updates and alerts from us related to'
                    ' the courses you are enrolled in. Sign In to continue.'
                )

            # Add message for later use.
            messages.success(
                request,
                HTML(message).format(
                    html_start=HTML('<p class="message-title">'),
                    html_end=HTML('</p>'),
                ),
                extra_tags='account-activation aa-icon',
            )

    return redirect('dashboard')


@ensure_csrf_cookie
def activate_account_studio(request, key):
    """
    When link in activation e-mail is clicked and the link belongs to studio.
    """
    try:
        registration = Registration.objects.get(activation_key=key)
    except (Registration.DoesNotExist, Registration.MultipleObjectsReturned):
        return render_to_response(
            "registration/activation_invalid.html",
            {'csrf': csrf(request)['csrf_token']}
        )
    else:
        user_logged_in = request.user.is_authenticated
        already_active = True
        if not registration.user.is_active:
            registration.activate()
            already_active = False

        return render_to_response(
            "registration/activation_complete.html",
            {
                'user_logged_in': user_logged_in,
                'already_active': already_active
            }
        )


def validate_new_email(user, new_email):
    """
    Given a new email for a user, does some basic verification of the new address If any issues are encountered
    with verification a ValueError will be thrown.
    """
    try:
        validate_email(new_email)
    except ValidationError:
        raise ValueError(_('Valid e-mail address required.'))

    if new_email == user.email:
        raise ValueError(_('Old email is the same as the new email.'))


def validate_secondary_email(user, new_email):
    """
    Enforce valid email addresses.
    """

    from openedx.core.djangoapps.user_api.accounts.api import get_email_validation_error, \
        get_secondary_email_validation_error

    if get_email_validation_error(new_email):
        raise ValueError(_('Valid e-mail address required.'))

    # Make sure that if there is an active recovery email address, that is not the same as the new one.
    if hasattr(user, "account_recovery"):
        if user.account_recovery.is_active and new_email == user.account_recovery.secondary_email:
            raise ValueError(_('Old email is the same as the new email.'))

    # Make sure that secondary email address is not same as user's primary email.
    if new_email == user.email:
        raise ValueError(_('Cannot be same as your sign in email address.'))

    message = get_secondary_email_validation_error(new_email)
    if message:
        raise ValueError(message)


def do_email_change_request(user, new_email, activation_key=None, secondary_email_change_request=False):
    """
    Given a new email for a user, does some basic verification of the new address and sends an activation message
    to the new address. If any issues are encountered with verification or sending the message, a ValueError will
    be thrown.
    """
    # if activation_key is not passing as an argument, generate a random key
    if not activation_key:
        activation_key = uuid.uuid4().hex

    confirm_link = reverse('confirm_email_change', kwargs={'key': activation_key, })

    if secondary_email_change_request:
        PendingSecondaryEmailChange.objects.update_or_create(
            user=user,
            defaults={
                'new_secondary_email': new_email,
                'activation_key': activation_key,
            }
        )
        confirm_link = reverse('activate_secondary_email', kwargs={'key': activation_key})
    else:
        PendingEmailChange.objects.update_or_create(
            user=user,
            defaults={
                'new_email': new_email,
                'activation_key': activation_key,
            }
        )

    use_https = theming_helpers.get_current_request().is_secure()

    site = Site.objects.get_current()
    message_context = get_base_template_context(site)
    message_context.update({
        'old_email': user.email,
        'new_email': new_email,
        'confirm_link': '{protocol}://{site}{link}'.format(
            protocol='https' if use_https else 'http',
            site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            link=confirm_link,
        ),
    })

    if secondary_email_change_request:
        msg = RecoveryEmailCreate().personalize(
            recipient=Recipient(user.username, new_email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )
    else:
        msg = EmailChange().personalize(
            recipient=Recipient(user.username, new_email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )

    try:
        ace.send(msg)
    except Exception:
        from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        log.error(u'Unable to send email activation link to user from "%s"', from_address, exc_info=True)
        raise ValueError(_('Unable to send email activation link. Please try again later.'))

    if not secondary_email_change_request:
        # When the email address change is complete, a "edx.user.settings.changed" event will be emitted.
        # But because changing the email address is multi-step, we also emit an event here so that we can
        # track where the request was initiated.
        tracker.emit(
            SETTING_CHANGE_INITIATED,
            {
                "setting": "email",
                "old": message_context['old_email'],
                "new": message_context['new_email'],
                "user_id": user.id,
            }
        )


@ensure_csrf_cookie
def activate_secondary_email(request, key):
    """
    This is called when the activation link is clicked. We activate the secondary email
    for the requested user.
    """
    try:
        pending_secondary_email_change = PendingSecondaryEmailChange.objects.get(activation_key=key)
    except PendingSecondaryEmailChange.DoesNotExist:
        return render_to_response("invalid_email_key.html", {})

    try:
        account_recovery = pending_secondary_email_change.user.account_recovery
    except AccountRecovery.DoesNotExist:
        account_recovery = AccountRecovery(user=pending_secondary_email_change.user)

    try:
        account_recovery.update_recovery_email(pending_secondary_email_change.new_secondary_email)
    except ValidationError:
        return render_to_response("secondary_email_change_failed.html", {
            'secondary_email': pending_secondary_email_change.new_secondary_email
        })

    pending_secondary_email_change.delete()

    return render_to_response("secondary_email_change_successful.html")


@ensure_csrf_cookie
def confirm_email_change(request, key):
    """
    User requested a new e-mail. This is called when the activation
    link is clicked. We confirm with the old e-mail, and update
    """
    with transaction.atomic():
        try:
            pec = PendingEmailChange.objects.get(activation_key=key)
        except PendingEmailChange.DoesNotExist:
            response = render_to_response("invalid_email_key.html", {})
            transaction.set_rollback(True)
            return response

        user = pec.user
        address_context = {
            'old_email': user.email,
            'new_email': pec.new_email
        }

        if len(User.objects.filter(email=pec.new_email)) != 0:
            response = render_to_response("email_exists.html", {})
            transaction.set_rollback(True)
            return response

        use_https = request.is_secure()
        if settings.FEATURES['ENABLE_MKTG_SITE']:
            contact_link = marketing_link('CONTACT')
        else:
            contact_link = '{protocol}://{site}{link}'.format(
                protocol='https' if use_https else 'http',
                site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
                link=reverse('contact'),
            )

        site = Site.objects.get_current()
        message_context = get_base_template_context(site)
        message_context.update({
            'old_email': user.email,
            'new_email': pec.new_email,
            'contact_link': contact_link,
            'from_address': configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
        })

        msg = EmailChangeConfirmation().personalize(
            recipient=Recipient(user.username, user.email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )

        u_prof = UserProfile.objects.get(user=user)
        meta = u_prof.get_meta()
        if 'old_emails' not in meta:
            meta['old_emails'] = []
        meta['old_emails'].append([user.email, datetime.datetime.now(UTC).isoformat()])
        u_prof.set_meta(meta)
        u_prof.save()
        # Send it to the old email...
        try:
            ace.send(msg)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to old address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': user.email})
            transaction.set_rollback(True)
            return response

        user.email = pec.new_email
        user.save()
        pec.delete()
        # And send it to the new email...
        msg.recipient = Recipient(user.username, pec.new_email)
        try:
            ace.send(msg)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to new address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': pec.new_email})
            transaction.set_rollback(True)
            return response

        response = render_to_response("email_change_successful.html", address_context)
        return response


@require_POST
@login_required
@ensure_csrf_cookie
def change_email_settings(request):
    """
    Modify logged-in user's setting for receiving emails from a course.
    """
    user = request.user

    course_id = request.POST.get("course_id")
    course_key = CourseKey.from_string(course_id)
    receive_emails = request.POST.get("receive_emails")
    if receive_emails:
        optout_object = Optout.objects.filter(user=user, course_id=course_key)
        if optout_object:
            optout_object.delete()
        log.info(
            u"User %s (%s) opted in to receive emails from course %s",
            user.username,
            user.email,
            course_id,
        )
        track.views.server_track(
            request,
            "change-email-settings",
            {"receive_emails": "yes", "course": course_id},
            page='dashboard',
        )
    else:
        Optout.objects.get_or_create(user=user, course_id=course_key)
        log.info(
            u"User %s (%s) opted out of receiving emails from course %s",
            user.username,
            user.email,
            course_id,
        )
        track.views.server_track(
            request,
            "change-email-settings",
            {"receive_emails": "no", "course": course_id},
            page='dashboard',
        )

    return JsonResponse({"success": True})


@ensure_csrf_cookie
def text_me_the_app(request):
    """
    Text me the app view.
    """
    text_me_fragment = TextMeTheAppFragmentView().render_to_fragment(request)
    context = {
        'nav_hidden': True,
        'show_dashboard_tabs': True,
        'show_program_listing': ProgramsApiConfig.is_enabled(),
        'fragment': text_me_fragment
    }

    return render_to_response('text-me-the-app.html', context)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def course_enrollment_info(request, id=None, stu_id=None):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        stu = User.objects.get(id=id)
        log.warning(stu)
        enroll_list = CourseEnrollment.objects.filter(user=stu)
        log.warning(enroll_list)
        test_obj = CourseEnrollmentInfo.objects.filter(course_enrolled__in=enroll_list)
        log.warning(test_obj)
        serializer = CourseEnrollmentInfoSerializer(test_obj, many=True)
        return JsonResponse({
            "data_list": serializer.data,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get list of enrollments info!",
            "success": True
        }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        if 'id' in data and data['id']:
            id = data['id']
            try:
                course_enrollment_info = CourseEnrollmentInfo.objects.get(id=id)
            except course_enrollment_info.DoesNotExist:
                return JsonResponse({"errorCode": "400",
                                     "executed": True,
                                     "message": "course_enrollment_info {} does not exist".format(id),
                                     "success": False}, status=200)
            else:
                course_enrollment_info.course_user_name = data['course_user_name']
                course_enrollment_info.course_user_password = data['course_user_password']
                course_enrollment_info.course_school_code = data['course_school_code']
                course_enrollment_info.created = data['created']
                course_enrollment_info.ended_date = data['ended_date']
                course_enrollment_info.description = data['description']
                course_enrollment_info.customer_service_id = data['customer_service']
                course_enrollment_info.save()
                return JsonResponse({
                    "errorCode": "201",
                    "executed": True,
                    "message": "Succeed to update a student course_enrollment_info!",
                    "success": True
                }, status=201)
        else:
            user_id = data['stu_id']
            user = User.objects.get(id=user_id)
            course_key = CourseKey.from_string(data['course_id'])
            try:
                enrollment = CourseEnrollment.enroll(user, course_key)
            except CourseEnrollmentException as err:
                return JsonResponse({"errorCode": "400",
                                     "executed": True,
                                     "message": err,
                                     "success": False}, status=200)

            data['course_enrolled'] = enrollment.id
            log.warning(data)
            serializer = CourseEnrollmentInfoSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "errorCode": "201",
                    "executed": True,
                    "message": serializer.data,
                    "success": True
                }, status=201)
            return JsonResponse({"errorCode": "401",
                                 "executed": True,
                                 "message": serializer.data,
                                 "success": False}, status=401)
    elif request.method == 'DELETE':
        if id and stu_id:
            try:
                course_enrollment_info = CourseEnrollmentInfo.objects.get(id=id)
                stu = User.objects.get(id=stu_id)
                course_key = CourseKey.from_string(course_enrollment_info.course_id)
                CourseEnrollment.unenroll(stu, course_key)
            except CourseEnrollmentInfo.DoesNotExist:
                return JsonResponse({"errorCode": "404",
                                     "executed": True,
                                     "message": "course_enrollment_info {} does not exist".format(id),
                                     "success": False}, status=200)
            except Exception as err:
                return JsonResponse({"errorCode": "500",
                                     "executed": True,
                                     "message": err,
                                     "success": False}, status=200)
            ret = course_enrollment_info.delete()
            log.warning(ret)
            return JsonResponse({"errorCode": "200",
                                 "executed": True,
                                 "message": "Deleted a student enrollment {}!".format(id),
                                 "success": True}, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def customer_service_info(request, pk=None):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        test_obj = CustomerService.objects.all().order_by('id')
        serializer = CustomerServiceSerializer(test_obj, many=True)
        return JsonResponse({
            "data_list": serializer.data,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get list of customer services!",
            "success": True
        }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        if 'id' in data and data['id']:
            id = data['id']
            try:
                cs_obj = CustomerService.objects.get(id=id)
            except CustomerService.DoesNotExist:
                return JsonResponse({"errorCode": "400",
                                     "executed": True,
                                     "message": "CustomerService with id {} does not exist".format(id),
                                     "success": False}, status=200)
            else:
                cs_obj.customer_service_name = data['customer_service_name']
                cs_obj.customer_service_info = data['customer_service_info']
                cs_obj.save()
                return JsonResponse({
                    "errorCode": "201",
                    "executed": True,
                    "message": "Succeed to update a customer service {}!".format(id),
                    "success": True
                }, status=201)
        else:
            serializer = CustomerServiceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "errorCode": "201",
                    "executed": True,
                    "message": serializer.data,
                    "success": True
                }, status=201)
            return JsonResponse({"errorCode": "401",
                                 "executed": True,
                                 "message": serializer.data,
                                 "success": False}, status=401)
    elif request.method == 'DELETE':
        instance = CustomerService.objects.get(id=pk)
        ret = instance.delete()
        log.warning(ret)
        return JsonResponse({"errorCode": "200",
                             "executed": True,
                             "message": "Deleted a customer service record with id {}!".format(pk),
                             "success": True}, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def students_search(request, key=None):
    """
    "phone_number": "",
    "username": "",
    "password": "test",
    "name": "",
    "web_accelerator_name": "洛杉矶",
    "web_accelerator_link": "http://47.114.176.127/test.pac",
    """
    if request.method == 'GET':
        list_user = User.objects.filter(Q(username__icontains=key) | Q(email__icontains=key))
        res_list = []
        try:
            for user in list_user:
                log.info("user object is {}".format(user))
                num = CourseEnrollment.objects.filter(user=user, is_active=1).count()
                user_obj = {
                    "user": {
                        "id": user.id,
                        "password": user.password,
                        "username": user.username
                    },
                    "phone_number": user.profile.phone_number,
                    "web_accelerator_name": user.profile.web_accelerator_name,
                    "web_accelerator_link": user.profile.web_accelerator_link,
                    "courses_count": num
                }
                res_list.append(user_obj)
        except Exception as err:
            log.error(err)
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": str(err),
                                 "success": False}, status=200)
        return JsonResponse({
            "data_list": res_list,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get students by searching.",
            "success": True
        })


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def students_management(request, pk=None):
    """
    "phone_number": "",
    "username": "",
    "password": "test",
    "name": "",
    "web_accelerator_name": "洛杉矶",
    "web_accelerator_link": "http://47.114.176.127/test.pac",
    """
    if request.method == 'GET':
        test_obj = UserProfile.objects.all().order_by('id')
        serializer = StudentSerializer(test_obj, many=True)
        return JsonResponse({
            "data_list": serializer.data,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get all the students!",
            "success": True
        }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        if 'id' in data and data['id']:
            id = data['id']
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return JsonResponse({"errorCode": "400",
                                     "executed": True,
                                     "message": "User with username {} does not exist".format(id),
                                     "success": False}, status=200)
            else:
                from common.djangoapps.util.password_policy_validators import normalize_password
                log.info("legacy password {}, new password {}".format(user.password, data['password']))
                if user.password != data['password']:
                    user.set_password(normalize_password(data["password"]))
                    log.info("new password {}".format(data['password']))
                user.username = data["username"]
                # user.update(username=data["username"])
                user.save()

                user_profile, profile_created = UserProfile.objects.update_or_create(
                    user=user, defaults={"name": data['name'],
                                         "web_accelerator_name": data['web_accelerator_name'],
                                         "web_accelerator_link": data['web_accelerator_link']},
                )
                return JsonResponse({
                    "id": user.id,
                    "username": user.username,
                    "phone_number": user_profile.phone_number,
                    "errorCode": "201",
                    "executed": True,
                    "message": "Succeed to update a student account!",
                    "success": True
                }, status=201)
        else:
            phone_number = data['phone_number']
            data['name'] = data['username']
            log.warning(data)
            user, user_pro = do_create_account_no_registration(data)
            if user is not None:
                return JsonResponse({
                    "id": user.id,
                    "username": user.username,
                    "phone_number": user_pro.phone_number,
                    "errorCode": "201",
                    "executed": True,
                    "message": "Succeed to create a student account!",
                    "success": True
                }, status=201)
            return JsonResponse({"phone_number": phone_number,
                                 "errorCode": "401",
                                 "executed": True,
                                 "message": "Failed to create student account!",
                                 "success": False}, status=401)

    elif request.method == 'DELETE':
        instance = User.objects.filter(id=pk)
        ret = instance.delete()
        log.warning(ret)
        return JsonResponse({"errorCode": "200",
                             "executed": True,
                             "message": "Deleted a student account!",
                             "success": True}, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def course_overview_info(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        test_obj = CourseOverview.objects.all().order_by('-modified')
        log.warning(str(test_obj))
        serializer = CourseOverviewSerializer(test_obj, many=True)
        return JsonResponse({
            "data_list": serializer.data,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get list of courses!",
            "success": True
        }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        course_overview_id = data['course_overview']
        log.warning(data)
        try:
            course_ext = CourseOverviewExtendInfo.objects.get(course_overview=course_overview_id)
        except CourseOverviewExtendInfo.DoesNotExist:
            log.warning("Course ext info of course {} not exist, create a new record!".format(course_overview_id))
            course_overview = CourseOverview.get_from_id(course_overview_id)
            course_ext = CourseOverviewExtendInfo(
                course_overview=course_overview,
                course_outside=data['course_outside'],
                course_link=data['course_link'],
                course_grade=data['course_grade'],
                course_price=data['course_price'],
                course_recommend_level=data['course_recommend_level'],
                course_highlight=data['course_highlight']
            )
        else:
            course_ext.course_outside = data['course_outside']
            course_ext.course_link = data['course_link']
            course_ext.course_grade = data['course_grade']
            course_ext.course_price = data['course_price']
            course_ext.course_recommend_level = data['course_recommend_level']
            course_ext.course_highlight = data['course_highlight']
        try:
            course_ext.save()
            return JsonResponse({
                "course_overview": data['course_overview'],
                "errorCode": "201",
                "executed": True,
                "message": "Succeed to update course to a direct access outside course!",
                "success": True
            }, status=201)
        except Exception:
            return JsonResponse({
                "course_overview": data['course_overview'],
                "errorCode": "401",
                "executed": True,
                "message": "Failed to update course!",
                "success": False
            }, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def course_overview_ccss_items_info(request, cour_id=None):
    if request.method == 'GET':
        if cour_id:
            try:
                course_ext = CourseOverviewExtendInfo.objects.get(id=cour_id)
                added_items_qs = course_ext.course_ccss_items.all().values('id')
                added_items = []
                for item in added_items_qs:
                    added_items.append(item['id'])
            except CourseOverviewExtendInfo.DoesNotExist:
                return JsonResponse({
                    "errorCode": "404",
                    "executed": True,
                    "message": "Course extend info does not exist {}!".format(cour_id),
                    "success": False}, status=200)
            return JsonResponse({
                "added_items": added_items,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get all existed items for course {}!".format(cour_id),
                "success": True
            }, status=200)
        else:
            gk_items = list(MapTestCheckItem.objects.filter(l3_grade="GK").order_by('id').values('id', 'item_name'))
            g1_items = list(MapTestCheckItem.objects.filter(l3_grade="G1").order_by('id').values('id', 'item_name'))
            g2_items = list(MapTestCheckItem.objects.filter(l3_grade="G2").order_by('id').values('id', 'item_name'))
            g3_items = list(MapTestCheckItem.objects.filter(l3_grade="G3").order_by('id').values('id', 'item_name'))
            g4_items = list(MapTestCheckItem.objects.filter(l3_grade="G4").order_by('id').values('id', 'item_name'))
            g5_items = list(MapTestCheckItem.objects.filter(l3_grade="G5").order_by('id').values('id', 'item_name'))
            g6_items = list(MapTestCheckItem.objects.filter(l3_grade="G6").order_by('id').values('id', 'item_name'))
            g7_items = list(MapTestCheckItem.objects.filter(l3_grade="G7").order_by('id').values('id', 'item_name'))
            g8_items = list(MapTestCheckItem.objects.filter(l3_grade="G8").order_by('id').values('id', 'item_name'))
            g9_g10_items = list(
                MapTestCheckItem.objects.filter(l3_grade="G9-G10").order_by('id').values('id', 'item_name'))
            g11_g12_items = list(
                MapTestCheckItem.objects.filter(l3_grade="G11-G12").order_by('id').values('id', 'item_name'))

            course_ids = list(CourseOverviewExtendInfo.objects.all().values('id', 'course_overview__display_name'))
            # for course_item in course_ids:
            #     course_item['id'] = str(course_item['id'])
            return JsonResponse({
                "gk_items": gk_items,
                "g1_items": g1_items,
                "g2_items": g2_items,
                "g3_items": g3_items,
                "g4_items": g4_items,
                "g5_items": g5_items,
                "g6_items": g6_items,
                "g7_items": g7_items,
                "g8_items": g8_items,
                "g9_g10_items": g9_g10_items,
                "g11_g12_items": g11_g12_items,
                "course_ids": course_ids,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get all the map test items!",
                "success": True
            }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        course_overview_id = data['course_overview']
        check_items = data['check_items']
        log.warning(data)
        try:
            course_ext = CourseOverviewExtendInfo.objects.get(id=course_overview_id)
        except CourseOverviewExtendInfo.DoesNotExist:
            return JsonResponse({
                "errorCode": "404",
                "executed": True,
                "message": "Course extend info does not exist {}!".format(course_overview_id),
                "success": False}, status=200)
        else:
            course_ext.course_ccss_items.clear()
            course_ext.course_ccss_items.add(*check_items)
            return JsonResponse({
                "errorCode": "201",
                "executed": True,
                "message": "Succeed to add ccss test items for course {}!".format(course_overview_id),
                "success": True
            }, status=201)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def my_map_test_info(request, phone):
    if request.method == 'GET':
        map_pro = list(MapStudentProfile.objects.filter(phone_number=phone).order_by('-TestDate')[:3])
        if len(map_pro) <= 0:
            log.error("No map test results for user {}".format(phone))
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "User with phone {} does not have any test result!".format(phone),
                                 "success": False}, status=200)
        else:
            rit_score = map_pro[0].Score
            test_duration = map_pro[0].TestDuration
            test_date = map_pro[0].TestDate
            map_pdf_url = map_pro[0].map_pdf_url
            achievement_above_mean = map_pro[0].achievement_above_mean
            lexile_score = map_pro[0].lexile_score
            flesch_kincaid_grade_level = map_pro[0].flesch_kincaid_grade_level
            growth_goals_date = map_pro[0].growth_goals_date

            map_score_trend_date = []
            map_score_trend_value = []
            for result in reversed(map_pro):
                map_score_trend_date.append(result.TestDate)
                map_score_trend_value.append(result.Score)

            suggested_area_of_focus = map_pro[0].suggested_area_of_focus_list
            if suggested_area_of_focus:
                suggested_area_of_focus_list = suggested_area_of_focus.split(',')
            relative_strength = map_pro[0].relative_strength_list
            if relative_strength:
                relative_strength_list = relative_strength.split(',')

            sub_domains_info_list = [
                {
                    "domain_name": "Literary Text: Key Ideas and Details",
                    "domain_score": map_pro[0].Literary_Text_Key_Ideas_and_Details_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Informational Text: Language, Craft, and Structure",
                    "domain_score": map_pro[0].Informational_Text_Language_Craft_and_Structure_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Literary Text: Language, Craft, and Structure",
                    "domain_score": map_pro[0].Literary_Text_Language_Craft_and_Structure_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Vocabulary: Acquisition and Use",
                    "domain_score": map_pro[0].Vocabulary_Acquisition_and_Use_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Informational Text: Key Ideas and Details",
                    "domain_score": map_pro[0].Informational_Text_Key_Ideas_and_Details_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Vocabulary Use and Functions",
                    "domain_score": map_pro[0].vocabulary_use_and_function,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language and Writing",
                    "domain_score": map_pro[0].language_and_writing,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Foundational Skills",
                    "domain_score": map_pro[0].foundational_skills,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Literature and Informational Text",
                    "domain_score": map_pro[0].literature_and_informational_text,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Writing: Write, Revise Texts for Purpose and Audience",
                    "domain_score": map_pro[0].writing_write_revise_texts_for_purpose_and_audience,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language: Understand, Edit for Mechanics",
                    "domain_score": map_pro[0].language_understand_edit_for_mechanics,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language: Understand, Edit for Grammar, Usage",
                    "domain_score": map_pro[0].language_understand_edit_for_grammar_usage,
                    "focus_strength_info": ""
                }
            ]
            if suggested_area_of_focus:
                for item in suggested_area_of_focus_list:
                    domain_index = int(item)
                    if domain_index < 12:
                        sub_domains_info_list[domain_index]["focus_strength_info"] = "Suggested Area of Focus"
            if relative_strength:
                for item in relative_strength_list:
                    domain_index = int(item)
                    if domain_index < 12:
                        sub_domains_info_list[domain_index]["focus_strength_info"] = "Relative Strength"
            if map_pro[0].Growth.startswith('Reading 2-5'):
                sub_domains_info = sub_domains_info_list[:5]
            elif map_pro[0].Growth.startswith('Reading K-2'):
                sub_domains_info = sub_domains_info_list[5:9]
            else:
                sub_domains_info = sub_domains_info_list[9:]

            return JsonResponse({
                "test_date": test_date,
                "test_duration": test_duration,
                "rit_score": rit_score,
                "achievement_above_mean": achievement_above_mean,
                "lexile_score": lexile_score,
                "flesch_kincaid_grade_level": flesch_kincaid_grade_level,
                "growth_goals_date": growth_goals_date,
                "map_score_trend_date": map_score_trend_date,
                "map_score_trend_value": map_score_trend_value,
                "sub_domains_info": sub_domains_info,
                "map_pdf_url": map_pdf_url,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get latest map result of user {}!".format(phone),
                "success": True
            }, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def stu_map_test_info(request, id):
    if request.method == 'GET':
        user_pro = UserProfile.objects.filter(user_id=id).first()
        map_pro = []
        if user_pro:
            phone = user_pro.phone_number
            log.info("user id {}, phone is {}".format(id, phone))
            map_pro = list(MapStudentProfile.objects.filter(phone_number=phone).order_by('-TestDate')[:3])
        if len(map_pro) <= 0:
            log.error("No map test results for user {}".format(id))
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "User with id {} does not have any test result!".format(id),
                                 "success": False}, status=200)
        else:
            rit_score = map_pro[0].Score
            test_duration = map_pro[0].TestDuration
            test_date = map_pro[0].TestDate
            map_pdf_url = map_pro[0].map_pdf_url
            map_pdf_url_all_items = map_pro[0].map_pdf_url_all_items
            map_pdf_url_all_items_no_txt = map_pro[0].map_pdf_url_all_items_no_txt
            achievement_above_mean = map_pro[0].achievement_above_mean
            lexile_score = map_pro[0].lexile_score
            flesch_kincaid_grade_level = map_pro[0].flesch_kincaid_grade_level
            growth_goals_date = map_pro[0].growth_goals_date
            map_score_trend_date = []
            map_score_trend_value = []
            for result in reversed(map_pro):
                map_score_trend_date.append(result.TestDate)
                map_score_trend_value.append(result.Score)

            suggested_area_of_focus = map_pro[0].suggested_area_of_focus_list
            if suggested_area_of_focus:
                suggested_area_of_focus_list = suggested_area_of_focus.split(',')
            relative_strength = map_pro[0].relative_strength_list
            if relative_strength:
                relative_strength_list = relative_strength.split(',')

            sub_domains_info_list = [
                {
                    "domain_name": "Literary Text: Key Ideas and Details",
                    "domain_score": map_pro[0].Literary_Text_Key_Ideas_and_Details_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Informational Text: Language, Craft, and Structure",
                    "domain_score": map_pro[0].Informational_Text_Language_Craft_and_Structure_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Literary Text: Language, Craft, and Structure",
                    "domain_score": map_pro[0].Literary_Text_Language_Craft_and_Structure_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Vocabulary: Acquisition and Use",
                    "domain_score": map_pro[0].Vocabulary_Acquisition_and_Use_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Informational Text: Key Ideas and Details",
                    "domain_score": map_pro[0].Informational_Text_Key_Ideas_and_Details_SCORE,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Vocabulary Use and Functions",
                    "domain_score": map_pro[0].vocabulary_use_and_function,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language and Writing",
                    "domain_score": map_pro[0].language_and_writing,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Foundational Skills",
                    "domain_score": map_pro[0].foundational_skills,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Literature and Informational Text",
                    "domain_score": map_pro[0].literature_and_informational_text,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Writing: Write, Revise Texts for Purpose and Audience",
                    "domain_score": map_pro[0].writing_write_revise_texts_for_purpose_and_audience,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language: Understand, Edit for Mechanics",
                    "domain_score": map_pro[0].language_understand_edit_for_mechanics,
                    "focus_strength_info": ""
                }, {
                    "domain_name": "Language: Understand, Edit for Grammar, Usage",
                    "domain_score": map_pro[0].language_understand_edit_for_grammar_usage,
                    "focus_strength_info": ""
                }
            ]
            if suggested_area_of_focus:
                for item in suggested_area_of_focus_list:
                    domain_index = int(item)
                    if domain_index < 12:
                        sub_domains_info_list[domain_index]["focus_strength_info"] = "Suggested Area of Focus"
            if relative_strength:
                for item in relative_strength_list:
                    domain_index = int(item)
                    if domain_index < 12:
                        sub_domains_info_list[domain_index]["focus_strength_info"] = "Relative Strength"
            if map_pro[0].Growth.startswith('Reading 2-5'):
                sub_domains_info = sub_domains_info_list[:5]
            elif map_pro[0].Growth.startswith('Reading K-2'):
                sub_domains_info = sub_domains_info_list[5:9]
            else:
                sub_domains_info = sub_domains_info_list[9:]

        return JsonResponse({
            "test_date": test_date,
            "test_duration": test_duration,
            "rit_score": rit_score,
            "map_score_trend_date": map_score_trend_date,
            "map_score_trend_value": map_score_trend_value,
            "achievement_above_mean": achievement_above_mean,
            "lexile_score": lexile_score,
            "flesch_kincaid_grade_level": flesch_kincaid_grade_level,
            "growth_goals_date": growth_goals_date,
            "sub_domains_info": sub_domains_info,
            "pdf1": map_pdf_url,
            "pdf2": map_pdf_url_all_items,
            "pdf3": map_pdf_url_all_items_no_txt,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get latest map result of user {}!".format(phone),
            "success": True
        }, status=200)


@login_required
@ensure_csrf_cookie
# @csrf_exempt
def my_i_picture_info(request, phone):
    if request.method == 'GET':
        map_pro = MapStudentProfile.objects.filter(phone_number=phone).order_by('-TestDate').first()
        if not map_pro:
            log.error("No map test results for user {}".format(phone))
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "User with phone {} does not have any test result!".format(phone),
                                 "success": False}, status=200)
        else:
            ext_list = MapProfileExtResults.objects.filter(map_student_profile=map_pro,
                                                           item_level__contains='DEVELOP').values(
                "check_item__item_name", "item_level", "check_item__item_desc")
            language_standards = []
            reading_foundational_skills = []
            reading_standards_informational_text = []
            reading_literature = []
            speaking_listening = []
            writing = []

            for item in ext_list:
                if item['check_item__item_name'].startswith('L'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    language_standards.append(check_item_and_course_info)
                if item['check_item__item_name'].startswith('RF'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    reading_foundational_skills.append(check_item_and_course_info)
                if item['check_item__item_name'].startswith('RI'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    reading_standards_informational_text.append(check_item_and_course_info)
                if item['check_item__item_name'].startswith('RL'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    reading_literature.append(check_item_and_course_info)
                if item['check_item__item_name'].startswith('SL'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    speaking_listening.append(check_item_and_course_info)
                if item['check_item__item_name'].startswith('W'):
                    check_item_and_course_info = get_course_and_ccss_items_map(item['check_item__item_name'])
                    writing.append(check_item_and_course_info)

            count_of_develop_items = [len(language_standards), len(reading_foundational_skills),
                                      len(reading_standards_informational_text), len(reading_literature),
                                      len(speaking_listening), len(writing)]
            return JsonResponse({
                "count_of_develop_items": count_of_develop_items,
                "language_standards": language_standards,
                "reading_foundational_skills": reading_foundational_skills,
                "reading_standards_informational_text": reading_standards_informational_text,
                "reading_literature": reading_literature,
                "speaking_listening": speaking_listening,
                "writing": writing,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get latest map result of user {}!".format(phone),
                "success": True
            }, status=200)


def get_course_and_ccss_items_map(item_name):
    check_item = MapTestCheckItem.objects.get(item_name=item_name)
    course_list = check_item.courseoverviewextendinfo_set.all()
    courses_info = []
    for course in course_list:
        courses_info.append({
            "course_grade": course.course_grade,
            "course_price": course.course_price,
            "course_recommend_level": course.course_recommend_level,
            "course_highlight": course.course_highlight,
            "course_image_url": course.course_overview.course_image_url,
            "course_display_name": course.course_overview.display_name,
        })
    check_item_and_course_info = {
        "item_name": item_name,
        "item_desc": check_item.item_desc,
        "courses_info": courses_info,
        "courses_info_count": len(courses_info)
    }

    return check_item_and_course_info
