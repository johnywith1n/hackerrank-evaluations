from google.cloud import datastore

NAMESPACE = 'HackerrankEvaluations'

# MUST USE NAMESPACE TO AVOID COLLISIONS WITH PORTAL
datastore_client = datastore.Client(namespace=NAMESPACE)

