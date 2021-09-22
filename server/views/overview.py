import logging

from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import (
    login_required,
)

from server.datastore_models.assignments import Assignment
from server.datastore_models.tests import Test

from server.hackerrank_client import client as hackerrank_client

from server.util import convert_timestamp_to_pacific_datetime

overview_blueprint = Blueprint('overview', __name__)


@overview_blueprint.route("/overview")
@login_required
def overview_home():
    assignments = Assignment.get_all_assignments()
    tests = Test.get_all_tests()
    test_id_question_id_mapping = {
        t[Test.test_id]: t[Test.question_id] for t in tests
    }
    test_id_name_mapping = {
        t[Test.test_id]: t[Test.name] for t in tests
    }
    assignments_by_test_user_and_date = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for a in assignments:
        test_id = a.get(Assignment.test_id)
        email = a.get(Assignment.assignee_email)
        date = int(a.get(Assignment.deadline))
        assignments_by_test_user_and_date[test_id][email][date].append(a)
    return render_template('overview.html',
                           assignments=assignments_by_test_user_and_date,
                           sorted=sorted,
                           test_id_question_id_mapping=test_id_question_id_mapping,
                           test_id_name_mapping=test_id_name_mapping,
                           convert_timestamp_to_pacific_datetime=convert_timestamp_to_pacific_datetime,
                           Assignment=Assignment,
                           CANDIDATE_CODE_REVIEW_EVALUATION_URL=hackerrank_client.CANDIDATE_CODE_REVIEW_EVALUATION_URL)


@overview_blueprint.route("/overview_update_evaluation_status", methods=['POST'])
@login_required
def update_evaluation_status():
    assignments = Assignment.get_all_assignments()
    if not assignments:
        return redirect(url_for('overview.overview_home'))

    assignments_by_test = defaultdict(list)
    for a in assignments:
        assignments_by_test[a[Assignment.test_id]].append(a)

    finished_assignments = []
    for test_id in assignments_by_test:
        candidates, error = hackerrank_client.get_candidates_for_evaluation(test_id)
        if error:
            flash('Unable to fetch hackerrank candidates', 'danger')
            return redirect(url_for('home.main'))

        candidate_ids = set([c['id'] for c in candidates])
        finished_assignments.extend([a for a in assignments if a.get(Assignment.candidate_id) not in candidate_ids])
    try:
        Assignment.bulk_delete([a.key for a in finished_assignments])
        flash('Removed finished evaluations', 'primary')
    except Exception as e:
        logging.exception(e)
        flash('Unable to update evaluations', 'danger')

    return redirect(url_for('overview.overview_home'))

