from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'program_enrollments.rest_api.v1.urls')

from lms.djangoapps.program_enrollments.rest_api.v1.urls import *
