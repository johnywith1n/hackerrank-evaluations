import time
from collections import namedtuple

from google.cloud import datastore
from server.datastore_client.client import datastore_client

AssignmentNamedTuple = namedtuple('Assignment', ['assignee_email', 'candidate_id', 'report_url', 'test_id'])


# expected to finish assignment in 3 days
TIME_PERIOD_UNTIL_EXPECTED_COMPLETION = 3 * 24 * 60 * 60


class AssignmentStatus:
    PENDING = 'Pending'
    FINISHED = 'Finished'


class Assignment:
    KIND = 'Assignment'

    KEY_ID_SEPARATOR = '-'

    # model properties
    assignee_email = 'assignee_email'
    candidate_id = 'candidate_id'
    report_url = 'report_url'
    status = 'status'
    deadline = 'deadline'
    test_id = 'test_id'
    create_ts = 'create_ts'

    @staticmethod
    def get(key):
        key = datastore_client.key(Assignment.KIND, key)
        entity = datastore_client.get(key)
        return entity

    def get_assignment_id(candidate_id, test_id):
        return '{}{}{}'.format(candidate_id, Assignment.KEY_ID_SEPARATOR, test_id)

    @staticmethod
    def bulk_create(assignments):
        entities = []
        cur_time = time.time()
        for assignment in assignments:
            entity_id = Assignment.get_assignment_id(assignment.candidate_id, assignment.test_id)
            entity_key = datastore_client.key(Assignment.KIND, entity_id)
            entity = datastore.Entity(key=entity_key)
            entity[Assignment.assignee_email] = assignment.assignee_email.lower()
            entity[Assignment.candidate_id] = assignment.candidate_id
            entity[Assignment.report_url] = assignment.report_url
            entity[Assignment.create_ts] = cur_time
            entity[Assignment.deadline] = cur_time + TIME_PERIOD_UNTIL_EXPECTED_COMPLETION
            entity[Assignment.test_id] = assignment.test_id
            entities.append(entity)
        datastore_client.put_multi(entities)
        return entities

    @staticmethod
    def get_assignments_for_assignee(assignee_email):
        query = datastore_client.query(kind=Assignment.KIND)
        query.add_filter(Assignment.assignee_email, '=', assignee_email.lower())
        return list(query.fetch())

    @staticmethod
    def get_assignments_for_test_keys_only(test_id):
        query = datastore_client.query(kind=Assignment.KIND)
        query.add_filter(Assignment.test_id, '=', test_id)
        query.keys_only()
        entities = list(query.fetch())
        return [e.key for e in entities]

    @staticmethod
    def get_candidates_without_assignments(candidate_ids, test_id):
        keys = []
        missing = []
        for c_id in candidate_ids:
            entity_id = Assignment.get_assignment_id(c_id, test_id)
            keys.append(datastore_client.key(Assignment.KIND, entity_id))
        datastore_client.get_multi(keys, missing=missing)
        return [x.key.name.split(Assignment.KEY_ID_SEPARATOR)[0] for x in missing]

    @staticmethod
    def bulk_delete(keys):
        datastore_client.delete_multi(keys)

    @staticmethod
    def get_all_assignments():
        return list(datastore_client.query(kind=Assignment.KIND).fetch())

    @staticmethod
    def get_all_assignments_keys_only():
        query = datastore_client.query(kind=Assignment.KIND)
        query.keys_only()
        entities = list(query.fetch())
        return [e.key for e in entities]
