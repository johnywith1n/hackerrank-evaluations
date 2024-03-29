import logging

import requests

import config


# fill in the blank with the test id
CANDIDATES_API_URL = 'https://www.hackerrank.com/x/api/v3/tests/{}/candidates'

# first blank is report url
# third blank is code review question id
CANDIDATE_CODE_REVIEW_EVALUATION_URL = '{}/detailed/{}'

STATUS_EVALUATION = 1

MIN_SCORE_TO_ASSIGN = 100


def get_candidates(test_id):
    api_url = CANDIDATES_API_URL.format(test_id)

    session = requests.Session()
    session.auth = (config.hackerrank_api_key(), '')

    candidates = []
    has_more = True
    offset = 0
    limit = 100
    while has_more:
        params = dict(limit=limit, offset=offset, fields='id,report_url,score', ats_state=STATUS_EVALUATION,
                      sort='-attempt_endtime')
        r = session.get(api_url, params=params)
        res_json = r.json()
        if r.status_code != 200:
            logging.error(res_json)
            return None, 'invalid response from hackerrank'
        has_more = res_json.get('next')
        offset = offset + limit
        candidates.extend(res_json.get('data'))
    return candidates, None


def get_candidates_for_evaluation(test_id):
    candidates, error = get_candidates(test_id)
    if error:
        return None, error

    return [c for c in candidates if c.get('score') >= MIN_SCORE_TO_ASSIGN], None
