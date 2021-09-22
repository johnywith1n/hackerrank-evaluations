import time

from google.cloud import datastore
from server.datastore_client.client import datastore_client

class Test:
    KIND = 'Test'

    # model properties
    name = 'name'
    test_id = 'test_id'
    question_id = 'question_id'
    create_ts = 'create_ts'

    @staticmethod
    def get(key):
        key = datastore_client.key(Test.KIND, key)
        entity = datastore_client.get(key)
        return entity

    @staticmethod
    def create(name, test_id, question_id):
        key = datastore_client.key(Test.KIND, test_id)
        test = datastore.Entity(key=key)
        test[Test.name] = name
        test[Test.test_id] = test_id
        test[Test.question_id] = question_id
        test[Test.create_ts] = time.time()
        datastore_client.put(test)
        return test

    @staticmethod
    def delete(test_id):
        from server.datastore_models.assignments import Assignment
        keys = Assignment.get_assignments_for_test_keys_only(test_id)
        keys.append(datastore_client.key(Test.KIND, test_id))
        datastore_client.delete_multi(keys)

    @staticmethod
    def get_all_tests():
        tests = list(datastore_client.query(kind=Test.KIND).fetch())
        tests.sort(key=lambda t: t[Test.create_ts])
        return tests

    @staticmethod
    def get_all_tests_mapped_by_id():
        tests = [
        {
            'test_id': t[Test.test_id],
            'question_id': t[Test.question_id],
            'name': t[Test.name],
            'create_ts': t[Test.create_ts],

        } for t in Test.get_all_tests()
        ]
        tests.sort(key=lambda t: t['create_ts'])
        tests = {
            t['test_id']: t for t in tests
        }
        return tests