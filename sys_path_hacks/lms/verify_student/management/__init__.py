from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.management')

from lms.djangoapps.verify_student.management import *
