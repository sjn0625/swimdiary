import mimetypes
import os
from pathlib import Path
from typing import Optional, Tuple

from werkzeug.utils import secure_filename

from config import EXPORT_CACHE_DIR, UPLOAD_DIR

try:
    import boto3
except Exception:  # pragma: no cover
    boto3 = None


class StorageService:
    def __init__(self, app):
        self.app = app
        self.backend = self._detect_backend()
        self.client = None
        if self.backend == 'r2' and boto3 is not None:
            self.client = boto3.client(
                's3',
                endpoint_url=self.app.config['R2_ENDPOINT'],
                aws_access_key_id=self.app.config['R2_ACCESS_KEY_ID'],
                aws_secret_access_key=self.app.config['R2_SECRET_ACCESS_KEY'],
                region_name='auto',
            )

    def _detect_backend(self) -> str:
        cfg = self.app.config
        if (
            cfg.get('STORAGE_BACKEND') == 'r2'
            and cfg.get('R2_ENDPOINT')
            and cfg.get('R2_BUCKET')
            and cfg.get('R2_ACCESS_KEY_ID')
            and cfg.get('R2_SECRET_ACCESS_KEY')
            and boto3 is not None
        ):
            return 'r2'
        return 'local'

    def _content_type(self, filename: str, content_type: Optional[str]) -> str:
        if content_type:
            return content_type
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or 'application/octet-stream'

    def upload_bytes(self, data: bytes, key: str, filename: str, content_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
        safe_name = secure_filename(filename) or 'file.bin'
        if self.backend == 'r2':
            self.client.put_object(
                Bucket=self.app.config['R2_BUCKET'],
                Key=key,
                Body=data,
                ContentType=self._content_type(safe_name, content_type),
            )
            public_base = self.app.config.get('R2_PUBLIC_BASE_URL')
            url = f"{public_base.rstrip('/')}/{key}" if public_base else None
            return key, url

        local_dir = UPLOAD_DIR if not key.startswith('exports/') else EXPORT_CACHE_DIR
        local_dir.mkdir(exist_ok=True, parents=True)
        file_path = local_dir / secure_filename(key.replace('/', '__'))
        file_path.write_bytes(data)
        return str(file_path), None

    def upload_file_storage(self, file_storage, key: str) -> Tuple[str, Optional[str]]:
        data = file_storage.read()
        file_storage.stream.seek(0)
        return self.upload_bytes(data, key=key, filename=file_storage.filename or 'upload.bin', content_type=file_storage.content_type)

