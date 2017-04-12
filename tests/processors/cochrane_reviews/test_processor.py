# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import uuid
import pytest
import processors.cochrane_reviews.processor as processor
pytest.mark.usefixtures('betamax_session')


class TestCochraneProcessor(object):
    def test_get_ref_identifiers(self):
        reference = {
            'layingaround': 'NCT    87654321',
            'identifiers': [
                {'type': 'OTHER', 'value': 'PMID should not be matched 1860386'},
                {'type': 'PUBMED', 'value': '12345678'},
            ]
        }
        identifiers = processor.extract_ref_identifiers(reference)
        expected = {
            'pubmed_id': '12345678',
            'nct_id': '87654321',
        }
        assert identifiers == expected


    def test_scrape_pubmed_id(self, betamax_session):
        reference = {
            'year': '2010',
            'title': ('Supported employment: randomised controlled trial'),
            'authors': ('Howard LM, Heslin M, Leese M, McCrone P, Rice C, Jarrett M, et al')
        }
        pubmed_url = ('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
                        'retmode=json&term=(supported employment randomised controlled trial) AND '
                        '(howard lm heslin m leese m mccrone p rice c jarrett m et al) AND (2010)')
        betamax_session.get(pubmed_url)
        pmid = processor.scrape_pubmed_id(reference)

        assert pmid == '20435968'


    def links_risk_of_bias_with_trial(self, conn, cochrane_review, trial_with_record):
        review_record = conn['warehouse']['cochrane_reviews'].find_one(id=cochrane_review)
        updated_reference = review_record['refs'][0]
        updated_reference.update({
            'identifiers': [{'type': 'other', 'value':'NCT24681012'}],
        })
        review_attrs = {
            'id': cochrane_review,
            'file_name': 'For publication',
            'refs': [updated_reference],
        }
        conn['warehouse']['cochrane_reviews'].update(review_attrs, ['id'])

        processor.process({}, conn)
        created_robs = [rob for rob in conn['database']['risk_of_biases'].all()]

        assert len(created_robs) == 1
        assert uuid.UUID(created_robs[0]['trial_id']).hex == trial_with_record


@pytest.fixture
def trial_with_record(conn, trial, record):
    trial_identifiers = {'nct': 'NCT24681012'}
    trial_attrs = {
        'id': trial,
        'identifiers': trial_identifiers,
    }
    record_attrs = {
        'id': record,
        'trial_id': trial,
        'identifiers': trial_identifiers,
    }
    conn['database']['records'].update(record_attrs, ['id'])
    conn['database']['trials'].update(trial_attrs, ['id'])
    return trial
