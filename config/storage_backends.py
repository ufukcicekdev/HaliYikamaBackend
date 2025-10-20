"""
Custom storage backends for AWS S3 / DigitalOcean Spaces
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for media files
    Stores all files in the 'haliyikama' folder on DigitalOcean Spaces
    """
    location = settings.AWS_LOCATION
    file_overwrite = False
    default_acl = settings.AWS_DEFAULT_ACL
