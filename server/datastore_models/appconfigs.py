from google.cloud import datastore
from server.datastore_client.client import datastore_client


class AppConfigKeys:
    TEST_ID = 'TEST_ID'
    QUESTION_ID = 'QUESTION_ID'


class AppConfig:
    KIND = 'AppConfig'

    # mapping of app config keys to their description
    APP_CONFIG_KEYs = {
        AppConfigKeys.TEST_ID: 'Test ID',
        AppConfigKeys.QUESTION_ID: 'Code Review Question ID'
    }

    # model properties
    key = 'key'
    value = 'value'

    @staticmethod
    def get(key):
        key = datastore_client.key(AppConfig.KIND, key)
        entity = datastore_client.get(key)
        return entity

    @staticmethod
    def upsert(config_key, value):
        entity_key = datastore_client.key(AppConfig.KIND, config_key)
        entity = datastore.Entity(key=entity_key)
        entity[AppConfig.value] = value
        datastore_client.put(entity)
        return entity

    @staticmethod
    def get_all_appconfig_keys():
        return AppConfig.APP_CONFIG_KEYs
