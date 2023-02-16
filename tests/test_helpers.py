import os


class TestHelpers:
    ENV_VARS = {
        'AWS_REGION': 'test_aws_region',
        'AWS_ACCESS_KEY_ID': 'test_aws_key_id',
        'AWS_SECRET_ACCESS_KEY': 'test_aws_secret_key',
        'SIERRA_DB_PORT': 'test_sierra_port',
        'SIERRA_DB_NAME': 'test_sierra_name',
        'SIERRA_DB_HOST': 'test_sierra_host',
        'SIERRA_DB_USER': 'test_sierra_user',
        'SIERRA_DB_PASSWORD': 'test_sierra_password',
        'REDIS_HOST': '127.0.0.1',
        'REDIS_PORT': '6739'
    }

    @classmethod
    def set_env_vars(cls):
        for key, value in cls.ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def clear_env_vars(cls):
        for key in cls.ENV_VARS.keys():
            if key in os.environ:
                del os.environ[key]
