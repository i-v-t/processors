# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import uuid
import logging
from .. import helpers
logger = logging.getLogger(__name__)


# Module API

def write_trial(conn, trial, source_id, record_id):
    """Write trial to database.

    Args:
        conn (dict): connection dict
        trial (dict): normilized trial data

    Raises:
        KeyError: if data structure is not valid

    Returns:
        (str, bool)/(None, None): trial id and is primary flag/if not written (skipped)

    """
    create = False

    # Get trial object (first try to ignore source record for better dedup)
    object = helpers.find_trial_by_identifiers(conn, trial['identifiers'],
        ignore_record_id=record_id)
    if not object:
        object = helpers.find_trial_by_identifiers(conn, trial['identifiers'])

    # Create object
    if not object:
        object = {}
        object['id'] = uuid.uuid1().hex
        create = True

    # Decide primary
    is_primary = False
    priority = ['nct', 'euctr', 'isrctn']
    for register in priority:
        if create:
            is_primary = True
            break
        elif object['source_id'] == source_id:
            is_primary = True
            break
        elif source_id == register:
            is_primary = True
            break
        elif object['source_id'] == register:
            is_primary = False
            break

    # BUG #389: Overwrite trials without records from the same source
    records_count = conn['database']['records'].count(
        trial_id=object['id'],
        source_id=object.get('source_id')
    )
    if records_count == 0:
        is_primary = True

    # Update data only if it's primary
    if is_primary:

        # Update object
        object.update({
            'source_id': source_id,
            # ---
            'identifiers': trial['identifiers'],
            'registration_date': trial.get('registration_date', None),
            'completion_date': trial.get('completion_date', None),
            'public_title': trial['public_title'],
            'brief_summary': trial.get('brief_summary', None),
            'scientific_title': trial.get('scientific_title', None),
            'description': trial.get('description', None),
            'status': trial.get('status'),
            'recruitment_status': trial.get('recruitment_status', None),
            'eligibility_criteria': trial.get('eligibility_criteria', None),
            'target_sample_size': trial.get('target_sample_size', None),
            'first_enrollment_date': trial.get('first_enrollment_date', None),
            'study_type': trial.get('study_type', None),
            'study_design': trial.get('study_design', None),
            'study_phase': trial.get('study_phase', None),
            'primary_outcomes': trial.get('primary_outcomes', None),
            'secondary_outcomes': trial.get('primary_outcomes', None),
            'gender': trial.get('gender', None),
            'has_published_results': trial.get('has_published_results', None),
            'results_exemption_date': trial.get('results_exemption_date'),
        })

    # Write object
    conn['database']['trials'].upsert(object, ['id'], ensure=False)

    # Log debug
    logger.debug('Trial - %s: %s',
        'created' if create else 'updated', trial['identifiers'])

    return object['id'], is_primary
