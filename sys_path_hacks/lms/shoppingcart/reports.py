from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.reports')

from lms.djangoapps.shoppingcart.reports import *
