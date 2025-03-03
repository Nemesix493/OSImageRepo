from pathlib import Path
from unittest import TestCase
from io import BytesIO
from os import makedirs
from shutil import rmtree

from api import app


class APITests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.test_upload_path = Path('./test-data').resolve()
        makedirs(cls.test_upload_path)
        cls.app.config.update({
            "TESTING": True,
            "UPLOAD_PATH": cls.test_upload_path
        })
        cls.test_file = {
            'directory': 'test/test',
            'name': 'test_file.txt',
            'content': b"test_test",
            'root': 'test'
        }
        cls.test_file['root_path'] = (cls.test_upload_path / cls.test_file['root']).resolve()
        cls.test_file['path'] = (
            cls.test_upload_path / cls.test_file['directory'] / cls.test_file['name']
        ).resolve()
        cls.test_file['directory_path'] = (cls.test_upload_path / cls.test_file['directory']).resolve()
        cls.client = app.test_client()
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.test_upload_path)
        return super().tearDownClass()

    def test_get_error(self):
        self.assertEqual(
            self.client.get('/test/').status_code,
            405
        )

    def test_put_error(self):
        self.assertEqual(
            self.client.put('/test/').status_code,
            405
        )

    def test_delete_error(self):
        self.assertEqual(
            self.client.delete('/test/').status_code,
            405
        )

    def check_a_test_file(self, test_file):
        self.assertTrue(
            test_file['path'].exists()
        )
        with open(test_file['path'], 'rb') as f:
            file_content = f.read()
        self.assertEqual(file_content, test_file['content'])

    def test_post_success(self):
        self.assertEqual(
            self.client.post(
                '/' + self.test_file['directory'],
                data={'files': (BytesIO(self.test_file['content']), self.test_file['name'])}
            ).status_code,
            201
        )
        self.check_a_test_file(self.test_file)
        rmtree((self.test_upload_path / self.test_file['root']))

    def test_post_error(self):
        makedirs(self.test_file['directory_path'])
        with open(self.test_file['path'], 'wb+') as file:
            file.write(self.test_file['content'])
        self.assertEqual(
            self.client.post(
                '/' + self.test_file['directory'],
                data={
                    'files': [
                        (BytesIO(self.test_file['content']), self.test_file['name']),
                        (BytesIO(b"some other data"), "another_file.txt")
                    ]
                }
            ).status_code,
            400
        )
        self.check_a_test_file(self.test_file)
        self.assertFalse((self.test_file['directory_path'] / "another_file.txt").resolve().exists())
        rmtree((self.test_upload_path / self.test_file['root']))
