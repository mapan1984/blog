import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    JSON_AS_ASCII = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hard_to_guess_string')

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

    CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0'
    CELERY_RESULT_BACKEND = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0'

    # Mail_Config
    MAIL_SUBJECT_PREFIX = '[HIDDEN-ISLAND]'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

    ARTICLES_SOURCE_DIR = os.path.join(BASE_DIR, 'articles')
    ARTICLES_PER_PAGE = 7
    COMMENTS_PER_PAGE = 7
    MAX_ARTICLE_SIZE = 16 * 1024 * 1024
    ALLOWED_FILE_EXTENSIONS = set(['md', 'markdown'])

    @classmethod
    def allowed_file(cls, filename):
        return '.' in filename \
               and filename.rsplit('.', 1)[1] in cls.ALLOWED_FILE_EXTENSIONS

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data.sqlite')

    @classmethod
    def init_app(cls, app_):
        Config.init_app(app_)

        # email errors to the administrators
        import logging
        from app.utils.log_handler import SendGridMailHandler
        mail_handler = SendGridMailHandler(
            recipient=cls.ADMIN_EMAIL,
            subject=cls.MAIL_SUBJECT_PREFIX + 'Application error!'
        )
        mail_handler.setFormatter(logging.Formatter('''
            Message type:       %(levelname)s
            Location:           %(pathname)s:%(lineno)d
            Module:             %(module)s
            Function:           %(funcName)s
            Time:               %(asctime)s

            Message:

            %(message)s
        '''))
        mail_handler.setLevel(logging.ERROR)
        app_.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    SQLALCHEMY_DATABASE_URI = 'postgresql://' + POSTGRES_USER + ':' + POSTGRES_PASSWORD + '@postgres:5432/' + POSTGRES_DB

    REDIS_HOST = os.getenv('DOCKER_REDIS_HOST', 'localhost')
    REDIS_PASSWORD = os.getenv('DOCKER_REDIS_PASSWORD', '')

    CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0'
    CELERY_RESULT_BACKEND = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0'

    # MYSQL_USER = os.environ.get('MYSQL_USER')
    # MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    # MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE')
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://' + MYSQL_USER + ':' + MYSQL_PASSWORD + '@mysql/' + MYSQL_DATABASE

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,

    'default': DevelopmentConfig
}
