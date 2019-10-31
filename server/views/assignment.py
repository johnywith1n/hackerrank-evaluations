import logging
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    current_user,
    login_required,
)

from server.datastore_models.users import UserPermissions
from server.hackerrank_client import client as hackerrank_client
from server.datastore_models.assignments import Assignment, AssignmentNamedTuple

assignment_blueprint = Blueprint('assignment', __name__)


def assign_perm_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not UserPermissions.has_perm(current_user.perms, UserPermissions.ASSIGN_EVALUATIONS):
            return abort(403)
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


@assignment_blueprint.route("/assign_evaluations", methods=['GET'])
@login_required
@assign_perm_required
def assign_home():
    return render_template('assignments.html')


@assignment_blueprint.route("/assign_evaluations", methods=['POST'])
@login_required
@assign_perm_required
def process_assignments():
    available_percentage = 100
    emails_with_no_percentage = []
    emails_with_overridden_percentage = set()
    email_to_percent = {}
    max_assignments_per_person = None
    for key, value in request.form.items():
        if key == 'max_assignments_per_person' and value:
            try:
                max_assignments_per_person = int(value)
                continue
            except:
                flash('Invalid number for max assignments per person {}'.format(value), 'danger')
                return redirect(url_for('assignment.assign_home'))

        email = key
        percent = value

        if not percent:
            emails_with_no_percentage.append(email)
        else:
            try:
                percent = int(percent)
            except:
                flash('Invalid percentage {}'.format(percent), 'danger')
                return redirect(url_for('assignment.assign_home'))
            emails_with_overridden_percentage.add(email)
            email_to_percent[email] = percent
            available_percentage = available_percentage - percent
            if available_percentage < 0:
                flash('Invalid percentage assignment', 'danger')
                return redirect(url_for('assignment.assign_home'))

    if emails_with_no_percentage:
        percentage_for_remaining_emails = available_percentage / len(emails_with_no_percentage)
        for email in emails_with_no_percentage:
            email_to_percent[email] = percentage_for_remaining_emails

    total_percentage = 0
    for percent in email_to_percent.values():
        total_percentage = total_percentage + percent

    if int(total_percentage) > 100:
        flash('Total percentage exceed 100', 'danger')
        return redirect(url_for('assignment.assign_home'))

    try:
        error = create_assignments(email_to_percent, emails_with_overridden_percentage,
                                   max_assignments_per_person=max_assignments_per_person)
        if error:
            flash('Unable to fetch hackerrank candidates', 'danger')
        else:
            flash('Assignments created', 'primary')
    except Exception as e:
        logging.exception(e)
        flash('Unable to create assignments', 'danger')
    return redirect(url_for('assignment.assign_home'))


def create_assignments(email_to_percent, emails_with_overridden_percentage, max_assignments_per_person=None):
    candidates, error = hackerrank_client.get_candidates_for_evaluation()
    if error:
        return error

    if max_assignments_per_person is not None:
        max_assignments = max_assignments_per_person * len(email_to_percent)
        if max_assignments < len(candidates):
            candidates = candidates[:max_assignments]

    candidate_ids = [c['id'] for c in candidates]
    unassigned_candidate_ids = Assignment.get_candidates_without_assignments(candidate_ids)
    candidates = [c for c in candidates if c['id'] in unassigned_candidate_ids]

    if not candidates:
        return None

    total_num_candidates = len(candidates)
    assignments_tuples = []
    for email, percentage in email_to_percent.items():
        percentage = percentage / 100
        num_candidates = int(total_num_candidates * percentage)
        # if it is 0, it will return the entire list so make it at least 1
        if num_candidates == 0:
            num_candidates = 1
        batch = candidates[-num_candidates:]
        del candidates[-num_candidates:]
        if batch:
            for candidate in batch:
                assignments_tuples.append(AssignmentNamedTuple(assignee_email=email, candidate_id=candidate['id'],
                                                               report_url=candidate['report_url']))
        if not candidates:
            break

    # if any left over, assign to each person one by one
    if candidates:
        index = 0
        unfiltered_emails = list(email_to_percent.keys())
        emails = [e for e in list(email_to_percent.keys()) if e not in emails_with_overridden_percentage]
        if not emails:
            emails = unfiltered_emails
        num_emails = len(emails)
        for candidate in candidates:
            assignments_tuples.append(AssignmentNamedTuple(assignee_email=emails[index % num_emails],
                                                           candidate_id=candidate['id'],
                                                           report_url=candidate['report_url']))
            index = index + 1

    Assignment.bulk_create(assignments_tuples)
    return None


@assignment_blueprint.route("/update_evaluation_status", methods=['POST'])
@login_required
def update_evaluation_status():
    assignments = Assignment.get_assignments_for_assignee(current_user.email)
    if not assignments:
        return redirect(url_for('home.main'))

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

    return redirect(url_for('home.main'))
