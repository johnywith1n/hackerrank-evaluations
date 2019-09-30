import logging

from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import (
    login_required,
)

from server.datastore_models.appconfigs import AppConfig, AppConfigKeys
from server.datastore_models.assignments import Assignment
from server.hackerrank_client import client as hackerrank_client

from server.util import convert_timestamp_to_pacific_datetime

overview_blueprint = Blueprint('overview', __name__)


@overview_blueprint.route("/overview")
@login_required
def overview_home():
    assignments = Assignment.get_all_assignments()
    code_review_test_id = AppConfig.get(AppConfigKeys.QUESTION_ID)
    if code_review_test_id:
        code_review_test_id = code_review_test_id.get(AppConfig.value)
    else:
        code_review_test_id = ''
    assignments_by_user_and_date = defaultdict(lambda: defaultdict(list))
    for a in assignments:
        date = int(a.get(Assignment.deadline))
        assignments_by_user_and_date[a.get(Assignment.assignee_email)][date].append(a)
    return render_template('overview.html',
                           sorted=sorted,
                           assignments_by_user_and_date=assignments_by_user_and_date,
                           code_review_test_id=code_review_test_id,
                           convert_timestamp_to_pacific_datetime=convert_timestamp_to_pacific_datetime,
                           Assignment=Assignment,
                           CANDIDATE_CODE_REVIEW_EVALUATION_URL=hackerrank_client.CANDIDATE_CODE_REVIEW_EVALUATION_URL)


@overview_blueprint.route("/overview_update_evaluation_status", methods=['POST'])
@login_required
def update_evaluation_status():
    assignments = Assignment.get_all_assignments()
    if not assignments:
        return redirect(url_for('overview.overview_home'))

    candidates, error = hackerrank_client.get_candidates_for_evaluation()
    if error:
        flash('Unable to fetch hackerrank candidates', 'danger')
        return redirect(url_for('home.main'))

    candidate_to_status_mapping = {
        c['id']: c['ats_state'] for c in candidates
    }

    finished_assignments = [a for a in assignments if candidate_to_status_mapping.get(
        a.get(Assignment.candidate_id)) != hackerrank_client.STATUS_EVALUATION]
    try:
        Assignment.bulk_delete([a.key for a in finished_assignments])
        flash('Removed finished evaluations', 'primary')
    except Exception as e:
        logging.exception(e)
        flash('Unable to update evaluations', 'danger')

    return redirect(url_for('overview.overview_home'))

