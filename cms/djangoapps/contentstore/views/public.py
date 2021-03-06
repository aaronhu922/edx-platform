"""
Public views
"""
import os

from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import urlquote_plus
from waffle.decorators import waffle_switch

from contentstore.config import waffle
from edxmako.shortcuts import render_to_response
from django.http import HttpResponse, JsonResponse
import logging

log = logging.getLogger(__name__)
__all__ = ['register_redirect_to_lms', 'login_redirect_to_lms', 'howitworks', 'accessibility', 'studentmanageapi']


def register_redirect_to_lms(request):
    """
    This view redirects to the LMS register view. It is used to temporarily keep the old
    Studio signup url alive.
    """
    register_url = '{register_url}{params}'.format(
        register_url=settings.FRONTEND_REGISTER_URL,
        params=_build_next_param(request),
    )
    return redirect(register_url, permanent=True)


def login_redirect_to_lms(request):
    """
    This view redirects to the LMS login view. It is used for Django's LOGIN_URL
    setting, which is where unauthenticated requests to protected endpoints are redirected.
    """
    login_url = '{login_url}{params}'.format(
        login_url=settings.FRONTEND_LOGIN_URL,
        params=_build_next_param(request),
    )
    return redirect(login_url)


def _build_next_param(request):
    """ Returns the next param to be used with login or register. """
    next_url = request.GET.get('next')
    next_url = next_url if next_url else settings.LOGIN_REDIRECT_URL
    if next_url:
        # Warning: do not use `build_absolute_uri` when `next_url` is empty because `build_absolute_uri` would
        # build use the login url for the next url, which would cause a login redirect loop.
        absolute_next_url = request.build_absolute_uri(next_url)
        return '?next=' + urlquote_plus(absolute_next_url)
    return ''


def howitworks(request):
    "Proxy view"
    if request.user.is_authenticated:
        return redirect('/home/')
    else:
        return render_to_response('howitworks.html', {})



def studentmanageapi(request):
    # response = HttpResponse()
    # construct the file's path
    url = settings.MANAGE_FRAMEWORK_HTML_PATH
    # test if path is ok and file exists
    if os.path.isfile(url):
        # let nginx determine the correct content type in this case
        # response['Content-Type'] = ""
        # response['X-Accel-Redirect'] = url
        # response['X-Sendfile'] = url
        # other webservers may accept X-Sendfile and not X-Accel-Redirect
        return HttpResponse(open(url).read())
    else:
        log.error("Front static file url is {}".format(url))
        return JsonResponse({"errorCode": "404",
                             "executed": True,
                             "message": "No html file returned!",
                             "success": False}, status=200)


@waffle_switch('{}.{}'.format(waffle.WAFFLE_NAMESPACE, waffle.ENABLE_ACCESSIBILITY_POLICY_PAGE))
def accessibility(request):
    """
    Display the accessibility accommodation form.
    """

    return render_to_response('accessibility.html', {
        'language_code': request.LANGUAGE_CODE
    })
