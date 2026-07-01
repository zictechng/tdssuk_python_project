from pathlib import Path
from django.core import signing

def build_upload_path(folder, instance, filename):
    identifier = str(getattr(instance, 'uuid', instance.pk))
    return f'{folder}/{identifier}/{filename}'


def document_upload_to(instance, filename):
    return build_upload_path('documents', instance, filename)


def delete_file(file_field):
    if not file_field:
        return
    if file_field.storage.exists(file_field.name):
        file_field.delete(save=False)


def encode_pk(pk, salt='role-pk'):
    return signing.dumps(pk, salt=salt)

def decode_pk(token, salt='role-pk'):
    try:
        return signing.loads(token, salt=salt, max_age=None)
    except Exception:
        return None