from google.cloud import datastore
from server.datastore_client.client import datastore_client

import config

USER_PERMS = dict(
    ADMIN='Admin',
    ASSIGN_EVALUATIONS='Assign Evaluations'
)


class UserPermissions:

    @staticmethod
    def has_perm(perms, perm_to_check):
        return perms and (perm_to_check in perms or UserPermissions.ADMIN in perms)

    @staticmethod
    def is_admin(perms):
        return perms and UserPermissions.ADMIN in perms


for perm in USER_PERMS:
    setattr(UserPermissions, perm, perm)


class User:
    KIND = 'User'

    email = 'email'
    perms = 'perms'

    @staticmethod
    def get(user_id):
        key = datastore_client.key(User.KIND, user_id)
        entity = datastore_client.get(key)
        return entity

    @staticmethod
    def create(user_id, email):
        key = datastore_client.key(User.KIND, user_id)
        user = datastore.Entity(key=key)
        user[User.email] = email

        if email == config.bootstrap_admin():
            user[User.perms] = [UserPermissions.ADMIN]
        datastore_client.put(user)
        return user

    @staticmethod
    def update(user):
        return datastore_client.put(user)

    @staticmethod
    def get_all_users():
        return list(datastore_client.query(kind=User.KIND).fetch())

    @staticmethod
    def get_all_user_emails():
        entities = list(datastore_client.query(kind=User.KIND, projection=[User.email]).fetch())
        return {e.key.name: e.get(User.email) for e in entities}

