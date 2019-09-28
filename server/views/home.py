from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    current_user,
    login_required,
)

from server.datastore_models.appconfigs import AppConfig, AppConfigKeys
from server.datastore_models.assignments import Assignment
from server.hackerrank_client.client import CANDIDATE_CODE_REVIEW_EVALUATION_URL

from server.util import convert_timestamp_to_pacific_datetime

home_blueprint = Blueprint('home', __name__)


@home_blueprint.route("/_ah/start")
def ah_start():
    return 'ok'


@home_blueprint.route("/home")
def main():
    if current_user.is_authenticated:
        assignments = Assignment.get_assignments_for_assignee(current_user.email)
        code_review_test_id = AppConfig.get(AppConfigKeys.QUESTION_ID)
        if code_review_test_id:
            code_review_test_id = code_review_test_id.get(AppConfig.value)
        else:
            code_review_test_id = ''
        assignments_by_date = defaultdict(list)
        for a in assignments:
            date = convert_timestamp_to_pacific_datetime(a.get(Assignment.deadline))
            assignments_by_date[date].append(a)
        return render_template('home.html',
                               assignments_by_date=assignments_by_date,
                               code_review_test_id=code_review_test_id,
                               Assignment=Assignment,
                               CANDIDATE_CODE_REVIEW_EVALUATION_URL=CANDIDATE_CODE_REVIEW_EVALUATION_URL)
    else:
        return '<a class="button" href="/login">Google Login</a>'


@home_blueprint.route("/")
def fake_home():
    return abort(404)

