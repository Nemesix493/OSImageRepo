from pathlib import Path
from unittest import TestCase
from io import BytesIO
from os import makedirs
from shutil import rmtree
from random import randbytes, choices
from string import ascii_letters, digits

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
        cls.client = app.test_client()
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.test_upload_path)
        return super().tearDownClass()

    # Helpers methods

    def get_random_name(self):
        return ''.join(choices(
            ascii_letters + digits,
            k=5
        ))

    def get_random_test_file(
            self,
            directory: list[str] | None = None,
            name: str | None = None,
            content: bytes | None = None):
        test_file = {
            'directory': directory,
            'name': name,
            'content': content
        }
        if directory is None:
            test_file['directory'] = [self.get_random_name() for i in range(3)]
        if name is None:
            test_file['name'] = self.get_random_name() + '.txt'
        if content is None:
            test_file['content'] = randbytes(10)
        test_file['root_path'] = (self.test_upload_path / test_file['directory'][0]).resolve()
        test_file['directory_path'] = (self.test_upload_path / '/'.join(test_file['directory'])).resolve()
        test_file['path'] = (test_file['directory_path'] / test_file['name']).resolve()
        return test_file

    def check_a_test_file(self, test_file):
        self.assertTrue(
            test_file['path'].exists()
        )
        with open(test_file['path'], 'rb') as f:
            file_content = f.read()
        self.assertEqual(file_content, test_file['content'])

    # Tests methods

    def test_get_success(self):
        test_file = self.get_random_test_file()
        directory_url = f'/{"/".join(test_file["directory"])}/'
        file_url = f'/{"/".join(test_file["directory"])}/{test_file["name"]}'

        # On none existing directory
        response = self.client.get(directory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Accel-Redirect'], '/files' + directory_url)

        # On none existing file
        response = self.client.get(file_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['X-Accel-Redirect'],
            '/files' + file_url
        )

        makedirs(test_file['directory_path'])
        with open(test_file['path'], 'wb+') as file:
            file.write(test_file['content'])

        # On existing directory
        response = self.client.get(directory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Accel-Redirect'], '/files' + directory_url)

        # On none existing file
        response = self.client.get(file_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['X-Accel-Redirect'],
            '/files' + file_url
        )

        # On root url
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['X-Accel-Redirect'],
            '/files/'
        )

        rmtree(test_file['directory_path'])

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

    def test_post_success(self):
        test_file = self.get_random_test_file()
        second_test_file = self.get_random_test_file(test_file['directory'])
        self.assertEqual(
            self.client.post(
                '/' + '/'.join(test_file['directory']),
                data={
                    'files': [
                        (BytesIO(test_file['content']), test_file['name']),
                        (BytesIO(second_test_file['content']), second_test_file['name'])
                    ]
                }
            ).status_code,
            201
        )
        self.check_a_test_file(second_test_file)
        self.check_a_test_file(test_file)
        rmtree(test_file['root_path'])

    def test_post_error(self):
        test_file = self.get_random_test_file()
        makedirs(test_file['directory_path'])
        with open(test_file['path'], 'wb+') as file:
            file.write(test_file['content'])
        another_test_file = self.get_random_test_file(test_file['directory'])
        self.assertEqual(
            self.client.post(
                '/' + '/'.join(test_file['directory']),
                data={
                    'files': [
                        (BytesIO(test_file['content']), test_file['name']),
                        (BytesIO(another_test_file['content']), another_test_file['name'])
                    ]
                }
            ).status_code,
            400
        )
        self.check_a_test_file(test_file)
        self.assertFalse(another_test_file['path'].exists())
        rmtree(test_file['directory_path'])

    def test_patch_success(self):
        test_file = self.get_random_test_file()
        makedirs(test_file['directory_path'])
        with open(test_file['path'], 'wb+') as file:
            file.write(test_file['content'])
        new_test_file = self.get_random_test_file(test_file['directory'])
        test_file['content'] = randbytes(9)
        self.assertEqual(
            self.client.patch(
                '/' + '/'.join(test_file['directory']),
                data={
                    'files': [
                        (BytesIO(test_file['content']), test_file['name']),
                        (BytesIO(new_test_file['content']), new_test_file['name'])
                    ]
                }
            ).status_code,
            200
        )
        self.check_a_test_file(test_file)
        self.check_a_test_file(new_test_file)
        rmtree(test_file['directory_path'])

    def test_patch_error(self):
        test_file = self.get_random_test_file()
        self.assertEqual(
            self.client.patch(
                '/' + '/'.join(test_file['directory']),
                data={
                    'files': [
                        (BytesIO(test_file['content']), test_file['name']),
                    ]
                }
            ).status_code,
            400
        )
        self.assertFalse(test_file['root_path'].exists())
