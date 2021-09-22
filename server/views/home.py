from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    current_user,
    login_required,
)

from server.datastore_models.assignments import Assignment
from server.datastore_models.tests import Test

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
        tests = Test.get_all_tests()
        test_id_question_id_mapping = {
            t[Test.test_id]: t[Test.question_id] for t in tests
        }
        test_id_name_mapping = {
            t[Test.test_id]: t[Test.name] for t in tests
        }

        assignments_by_test_and_date = defaultdict(lambda: defaultdict(list))
        for a in assignments:
            test_id = a.get(Assignment.test_id)
            date = int(a.get(Assignment.deadline))
            assignments_by_test_and_date[test_id][date].append(a)
        return render_template('home.html',
                               assignments=assignments_by_test_and_date,
                               test_id_question_id_mapping=test_id_question_id_mapping,
                               test_id_name_mapping=test_id_name_mapping,
                               sorted=sorted,
                               convert_timestamp_to_pacific_datetime=convert_timestamp_to_pacific_datetime,
                               Assignment=Assignment,
                               CANDIDATE_CODE_REVIEW_EVALUATION_URL=CANDIDATE_CODE_REVIEW_EVALUATION_URL)
    else:
        return '<a class="button" href="/login">Google Login</a>'


@home_blueprint.route("/")
def fake_home():
    return abort(404)

