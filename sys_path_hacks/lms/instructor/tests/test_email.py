from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.tests.test_email')

from lms.djangoapps.instructor.tests.test_email import *
