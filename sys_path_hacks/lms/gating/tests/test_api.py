from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'gating.tests.test_api')

from lms.djangoapps.gating.tests.test_api import *
