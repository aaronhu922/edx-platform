"""
Django module for Course Metadata class -- manages advanced settings and related parameters
"""


from datetime import datetime
import six
from crum import get_current_user
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import ugettext as _
import pytz
from six import text_type
from xblock.fields import Scope

from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG
from student.roles import GlobalStaff
from openedx.core.lib.teams_config import TeamsetType
from xblock_django.models import XBlockStudioConfigurationFlag
from xmodule.modulestore.django import modulestore


class CourseMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    # The list of fields that wouldn't be shown in Advanced Settings.
    # Should not be used directly. Instead the get_exclude_list_of_fields method should
    # be used if the field needs to be filtered depending on the feature flag.
    FIELDS_EXCLUDE_LIST = [
        'cohort_config',
        'xml_attributes',
        'start',
        'end',
        'enrollment_start',
        'enrollment_end',
        'certificate_available_date',
        'tabs',
        'graceperiod',
        'show_timezone',
        'format',
        'graded',
        'hide_from_toc',
        'pdf_textbooks',
        'user_partitions',
        'name',  # from xblock
        'tags',  # from xblock
        'visible_to_staff_only',
        'group_access',
        'pre_requisite_courses',
        'entrance_exam_enabled',
        'entrance_exam_minimum_score_pct',
        'entrance_exam_id',
        'is_entrance_exam',
        'in_entrance_exam',
        'language',
        'certificates',
        'minimum_grade_credit',
        'default_time_limit_minutes',
        'is_proctored_enabled',
        'is_time_limited',
        'is_practice_exam',
        'exam_review_rules',
        'hide_after_due',
        'self_paced',
        'show_correctness',
        'chrome',
        'default_tab',
        'highlights_enabled_for_messaging',
        'is_onboarding_exam',
    ]

    @classmethod
    def get_exclude_list_of_fields(cls, course_key):
        """
        Returns a list of fields to exclude from the Studio Advanced settings based on a
        feature flag (i.e. enabled or disabled).
        """
        # Copy the filtered list to avoid permanently changing the class attribute.
        exclude_list = list(cls.FIELDS_EXCLUDE_LIST)

        # Do not show giturl if feature is not enabled.
        if not settings.FEATURES.get('ENABLE_EXPORT_GIT'):
            exclude_list.append('giturl')

        # Do not show edxnotes if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_EDXNOTES'):
            exclude_list.append('edxnotes')

        # Do not show video auto advance if the feature is disabled
        if not settings.FEATURES.get('ENABLE_OTHER_COURSE_SETTINGS'):
            exclude_list.append('other_course_settings')

        # Do not show video_upload_pipeline if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_VIDEO_UPLOAD_PIPELINE'):
            exclude_list.append('video_upload_pipeline')

        # Do not show video auto advance if the feature is disabled
        if not settings.FEATURES.get('ENABLE_AUTOADVANCE_VIDEOS'):
            exclude_list.append('video_auto_advance')

        # Do not show social sharing url field if the feature is disabled.
        if (not hasattr(settings, 'SOCIAL_SHARING_SETTINGS') or
                not getattr(settings, 'SOCIAL_SHARING_SETTINGS', {}).get("CUSTOM_COURSE_URLS")):
            exclude_list.append('social_sharing_url')

        # Do not show teams configuration if feature is disabled.
        if not settings.FEATURES.get('ENABLE_TEAMS'):
            exclude_list.append('teams_configuration')

        if not settings.FEATURES.get('ENABLE_VIDEO_BUMPER'):
            exclude_list.append('video_bumper')

        # Do not show enable_ccx if feature is not enabled.
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX'):
            exclude_list.append('enable_ccx')
            exclude_list.append('ccx_connector')

        # Do not show "Issue Open Badges" in Studio Advanced Settings
        # if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_OPENBADGES'):
            exclude_list.append('issue_badges')

        # If the XBlockStudioConfiguration table is not being used, there is no need to
        # display the "Allow Unsupported XBlocks" setting.
        if not XBlockStudioConfigurationFlag.is_enabled():
            exclude_list.append('allow_unsupported_xblocks')

        # Do not show "Course Visibility For Unenrolled Learners" in Studio Advanced Settings
        # if the enable_anonymous_access flag is not enabled
        if not COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.is_enabled(course_key=course_key):
            exclude_list.append('course_visibility')

        # Do not show "Create Zendesk Tickets For Suspicious Proctored Exam Attempts" in
        # Studio Advanced Settings if the user is not edX staff.
        if not GlobalStaff().has_user(get_current_user()):
            exclude_list.append('create_zendesk_tickets')

        # Do not show "Proctortrack Exam Escalation Contact" if Proctortrack is not
        # an available proctoring backend.
        if not settings.PROCTORING_BACKENDS or settings.PROCTORING_BACKENDS.get('proctortrack') is None:
            exclude_list.append('proctoring_escalation_email')

        return exclude_list

    @classmethod
    def fetch(cls, descriptor):
        """
        Fetch the key:value editable course details for the given course from
        persistence and return a CourseMetadata model.
        """
        result = {}
        metadata = cls.fetch_all(descriptor)
        exclude_list_of_fields = cls.get_exclude_list_of_fields(descriptor.id)

        for key, value in six.iteritems(metadata):
            if key in exclude_list_of_fields:
                continue
            result[key] = value
        return result

    @classmethod
    def fetch_all(cls, descriptor):
        """
        Fetches all key:value pairs from persistence and returns a CourseMetadata model.
        """
        result = {}
        for field in descriptor.fields.values():
            if field.scope != Scope.settings:
                continue

            field_help = _(field.help)
            help_args = field.runtime_options.get('help_format_args')
            if help_args is not None:
                field_help = field_help.format(**help_args)

            result[field.name] = {
                'value': field.read_json(descriptor),
                'display_name': _(field.display_name),
                'help': field_help,
                'deprecated': field.runtime_options.get('deprecated', False),
                'hide_on_enabled_publisher': field.runtime_options.get('hide_on_enabled_publisher', False)
            }
        return result

    @classmethod
    def update_from_json(cls, descriptor, jsondict, user, filter_tabs=True):
        """
        Decode the json into CourseMetadata and save any changed attrs to the db.

        Ensures none of the fields are in the exclude list.
        """
        exclude_list_of_fields = cls.get_exclude_list_of_fields(descriptor.id)
        # Don't filter on the tab attribute if filter_tabs is False.
        if not filter_tabs:
            exclude_list_of_fields.remove("tabs")

        # Validate the values before actually setting them.
        key_values = {}

        for key, model in six.iteritems(jsondict):
            # should it be an error if one of the filtered list items is in the payload?
            if key in exclude_list_of_fields:
                continue
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError) as err:
                raise ValueError(_(u"Incorrect format for field '{name}'. {detailed_message}").format(
                    name=model['display_name'], detailed_message=text_type(err)))

        return cls.update_from_dict(key_values, descriptor, user)

    @classmethod
    def validate_and_update_from_json(cls, descriptor, jsondict, user, filter_tabs=True):
        """
        Validate the values in the json dict (validated by xblock fields from_json method)

        If all fields validate, go ahead and update those values on the object and return it without
        persisting it to the DB.
        If not, return the error objects list.

        Returns:
            did_validate: whether values pass validation or not
            errors: list of error objects
            result: the updated course metadata or None if error
        """
        exclude_list_of_fields = cls.get_exclude_list_of_fields(descriptor.id)

        if not filter_tabs:
            exclude_list_of_fields.remove("tabs")

        filtered_dict = dict((k, v) for k, v in six.iteritems(jsondict) if k not in exclude_list_of_fields)
        did_validate = True
        errors = []
        key_values = {}
        updated_data = None

        for key, model in six.iteritems(filtered_dict):
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError, ValidationError) as err:
                did_validate = False
                errors.append({'key': key, 'message': text_type(err), 'model': model})

        team_setting_errors = cls.validate_team_settings(filtered_dict)
        if team_setting_errors:
            errors = errors + team_setting_errors
            did_validate = False

        proctoring_errors = cls.validate_proctoring_settings(descriptor, filtered_dict, user)
        if proctoring_errors:
            errors = errors + proctoring_errors
            did_validate = False

        # If did validate, go ahead and update the metadata
        if did_validate:
            updated_data = cls.update_from_dict(key_values, descriptor, user, save=False)

        return did_validate, errors, updated_data

    @classmethod
    def update_from_dict(cls, key_values, descriptor, user, save=True):
        """
        Update metadata descriptor from key_values. Saves to modulestore if save is true.
        """
        for key, value in six.iteritems(key_values):
            setattr(descriptor, key, value)

        if save and key_values:
            modulestore().update_item(descriptor, user.id)

        return cls.fetch(descriptor)

    @classmethod
    def validate_team_settings(cls, settings_dict):
        """
        Validates team settings

        :param settings_dict: json dict containing all advanced settings
        :return: a list of error objects
        """
        errors = []
        teams_configuration_model = settings_dict.get('teams_configuration', {})
        if teams_configuration_model == {}:
            return errors
        json_value = teams_configuration_model.get('value')
        if json_value == '':
            return errors

        proposed_max_team_size = json_value.get('max_team_size')
        if proposed_max_team_size != '' and proposed_max_team_size is not None:
            if proposed_max_team_size <= 0:
                message = 'max_team_size must be greater than zero'
                errors.append({'key': 'teams_configuration', 'message': message, 'model': teams_configuration_model})
            elif proposed_max_team_size > 500:
                message = 'max_team_size cannot be greater than 500'
                errors.append({'key': 'teams_configuration', 'message': message, 'model': teams_configuration_model})

        proposed_topics = json_value.get('topics')

        if proposed_topics is None:
            proposed_teamsets = json_value.get('team_sets')
            if proposed_teamsets is None:
                return errors
            else:
                proposed_topics = proposed_teamsets

        proposed_topic_ids = [proposed_topic['id'] for proposed_topic in proposed_topics]
        proposed_topic_dupe_ids = {x for x in proposed_topic_ids if proposed_topic_ids.count(x) > 1}
        if len(proposed_topic_dupe_ids) > 0:
            message = 'duplicate ids: ' + ','.join(proposed_topic_dupe_ids)
            errors.append({'key': 'teams_configuration', 'message': message, 'model': teams_configuration_model})

        for proposed_topic in proposed_topics:
            topic_validation_errors = cls.validate_single_topic(proposed_topic)
            if topic_validation_errors:
                topic_validation_errors['model'] = teams_configuration_model
                errors.append(topic_validation_errors)

        return errors

    @classmethod
    def validate_single_topic(cls, topic_settings):
        """
        Helper method that validates a single teamset setting.
        The following conditions result in errors:
        > unrecognized extra keys
        > max_team_size <= 0
        > no name, id or description property
        > unrecognized teamset type
        :param topic_settings: the proposed settings being validated
        :return: an error object if error exists, otherwise None
        """
        error_list = []
        valid_teamset_types = [TeamsetType.open.value, TeamsetType.public_managed.value,
                               TeamsetType.private_managed.value]
        valid_keys = {'id', 'name', 'description', 'max_team_size', 'type'}
        teamset_type = topic_settings.get('type', {})
        if teamset_type:
            if teamset_type not in valid_teamset_types:
                error_list.append('type ' + teamset_type + " is invalid")
        max_team_size = topic_settings.get('max_team_size', {})
        if max_team_size:
            if max_team_size <= 0:
                error_list.append('max_team_size must be greater than zero')
            elif max_team_size > 500:
                error_list.append('max_team_size cannot be greater than 500')
        teamset_id = topic_settings.get('id', {})
        if not teamset_id:
            error_list.append('id attribute must not be empty')
        teamset_name = topic_settings.get('name', {})
        if not teamset_name:
            error_list.append('name attribute must not be empty')
        teamset_desc = topic_settings.get('description', {})
        if not teamset_desc:
            error_list.append('description attribute must not be empty')

        keys = set(topic_settings.keys())
        key_difference = keys - valid_keys
        if len(key_difference) > 0:
            error_list.append('extra keys: ' + ','.join(key_difference))

        if error_list:
            error = {'key': 'teams_configuration', 'message': ','.join(error_list)}
            return error

        return None

    @classmethod
    def validate_proctoring_settings(cls, descriptor, settings_dict, user):
        """
        Verify proctoring settings

        Returns a list of error objects
        """
        errors = []

        # If the user is not edX staff, the user has requested a change to the proctoring_provider
        # Advanced Setting, and it is after course start, prevent the user from changing the
        # proctoring provider.
        proctoring_provider_model = settings_dict.get('proctoring_provider', {})
        if (
            not user.is_staff and
            cls._has_requested_proctoring_provider_changed(
                descriptor.proctoring_provider, proctoring_provider_model.get('value')
            ) and
            datetime.now(pytz.UTC) > descriptor.start
        ):
            message = (
                'The proctoring provider cannot be modified after a course has started.'
                ' Contact {support_email} for assistance'
            ).format(support_email=settings.PARTNER_SUPPORT_EMAIL or 'support')
            errors.append({'key': 'proctoring_provider', 'message': message, 'model': proctoring_provider_model})

        # Require a valid escalation email if Proctortrack is chosen as the proctoring provider
        escalation_email_model = settings_dict.get('proctoring_escalation_email')
        if escalation_email_model:
            escalation_email = escalation_email_model.get('value')
        else:
            escalation_email = descriptor.proctoring_escalation_email

        missing_escalation_email_msg = 'Provider \'{provider}\' requires an exam escalation contact.'
        if proctoring_provider_model and proctoring_provider_model.get('value') == 'proctortrack':
            if not escalation_email:
                message = missing_escalation_email_msg.format(provider=proctoring_provider_model.get('value'))
                errors.append({
                    'key': 'proctoring_provider',
                    'message': message,
                    'model': proctoring_provider_model
                })

        if (
            escalation_email_model and not proctoring_provider_model and
            descriptor.proctoring_provider == 'proctortrack'
        ):
            if not escalation_email:
                message = missing_escalation_email_msg.format(provider=descriptor.proctoring_provider)
                errors.append({
                    'key': 'proctoring_escalation_email',
                    'message': message,
                    'model': escalation_email_model
                })

        return errors

    @staticmethod
    def _has_requested_proctoring_provider_changed(current_provider, requested_provider):
        """
        Return whether the requested proctoring provider is different than the current proctoring provider, indicating
        that the user has requested a change to the proctoring_provider Advanced Setting.
        """
        if requested_provider is None:
            return False
        else:
            return current_provider != requested_provider
