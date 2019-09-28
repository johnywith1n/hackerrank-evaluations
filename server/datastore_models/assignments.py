import time
from collections import namedtuple

from google.cloud import datastore
from server.datastore_client.client import datastore_client

AssignmentNamedTuple = namedtuple('Assignment', ['assignee_email', 'candidate_id', 'report_url'])


# expected to finish assignment in 3 days
TIME_PERIOD_UNTIL_EXPECTED_COMPLETION = 3 * 24 * 60 * 60


class AssignmentStatus:
    PENDING = 'Pending'
    FINISHED = 'Finished'


class Assignment:
    KIND = 'Assignment'

    # model properties
    assignee_email = 'assignee_email'
    candidate_id = 'candidate_id'
    report_url = 'report_url'
    status = 'status'
    deadline = 'deadline'
    create_ts = 'create_ts'

    @staticmethod
    def get(key):
        key = datastore_client.key(Assignment.KIND, key)
        entity = datastore_client.get(key)
        return entity

    @staticmethod
    def bulk_create(assignments):
        entities = []
        cur_time = time.time()
        for assignment in assignments:
            entity_key = datastore_client.key(Assignment.KIND, assignment.candidate_id)
            entity = datastore.Entity(key=entity_key)
            entity[Assignment.assignee_email] = assignment.assignee_email.lower()
            entity[Assignment.candidate_id] = assignment.candidate_id
            entity[Assignment.report_url] = assignment.report_url
            entity[Assignment.create_ts] = cur_time
            entity[Assignment.deadline] = cur_time + TIME_PERIOD_UNTIL_EXPECTED_COMPLETION
            entities.append(entity)
        datastore_client.put_multi(entities)
        return entities

    @staticmethod
    def get_assignments_for_assignee(assignee_email):
        query = datastore_client.query(kind=Assignment.KIND)
        query.add_filter(Assignment.assignee_email, '=', assignee_email.lower())
        return list(query.fetch())

    @staticmethod
    def get_candidates_without_assignments(candidate_ids):
        keys = []
        missing = []
        for c_id in candidate_ids:
            keys.append(datastore_client.key(Assignment.KIND, c_id))
        datastore_client.get_multi(keys, missing=missing)
        return [x.key.name for x in missing]

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
