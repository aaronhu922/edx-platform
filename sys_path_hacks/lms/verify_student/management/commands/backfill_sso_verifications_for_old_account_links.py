from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.management.commands.backfill_sso_verifications_for_old_account_links')

from lms.djangoapps.verify_student.management.commands.backfill_sso_verifications_for_old_account_links import *
