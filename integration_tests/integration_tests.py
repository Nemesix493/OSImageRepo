from unittest import (
    TestCase,
    TextTestRunner,
    TestLoader
)
from argparse import ArgumentParser
from io import BytesIO
from random import randbytes, choices
from string import ascii_letters, digits

import requests


class OSImageRepoTests(TestCase):
    tests_order = {
        'test_get_error': 1,
        'test_patch_error': 2,
        'test_post_success': 3,
        'test_post_error': 4,
        'test_patch_success': 5,
        'test_get_success': 6,
        'test_file_integrity': 7
    }
    DATA_TEST_BYTES_SIZE = 100
    test_files = []

    @classmethod
    def order(cls, test1, test2):
        return cls.tests_order[test1] - cls.tests_order[test2]

    @classmethod
    def get_url(cls):
        parser = ArgumentParser()
        parser.add_argument('-u', '--url', dest='url', help="URL of test deployement", required=True)
        cls.test_app_url = parser.parse_args().url

    @staticmethod
    def get_random_name():
        return ''.join(choices(
            ascii_letters + digits,
            k=5
        ))

    @classmethod
    def add_test_file(cls):
        test_file = {
            'content': randbytes(cls.DATA_TEST_BYTES_SIZE)
        }
        if len(cls.test_files) == 0:
            test_file['directory'] = [cls.get_random_name() for i in range(3)]
        else:
            test_file['directory'] = cls.test_files[0]['directory']
        test_file['name'] = cls.get_random_name() + '.txt'
        while test_file['name'] in [file['name'] for file in cls.test_files]:
            test_file['name'] = cls.get_random_name() + '.txt'
        test_file['dir_url'] = cls.test_app_url + '/'.join(test_file['directory']) + '/'
        test_file['url'] = test_file['dir_url'] + test_file['name']
        cls.test_files.append(test_file)

    @classmethod
    def get_test_data(cls):
        [cls.add_test_file() for i in range(4)]

    @classmethod
    def setUpClass(cls):
        cls.get_url()
        cls.get_test_data()
        return super().setUpClass()

    def test_get_success(self):
        for test_file in self.test_files:
            response = requests.get(
               test_file['url']
            )
            self.assertEqual(response.status_code, 200)
            test_file['download_content'] = response.content

    def test_get_error(self):
        self.assertEqual(
            requests.get(self.test_files[0]['dir_url']).status_code,
            404
        )
        self.assertEqual(
            requests.get(self.test_files[0]['url']).status_code,
            404
        )

    def test_post_success(self):
        self.assertEqual(
            requests.post(
                self.test_files[0]['dir_url'],
                files={
                    'file_0': (self.test_files[0]['name'], BytesIO(self.test_files[0]['content'])),
                    'file_1': (self.test_files[1]['name'], BytesIO(self.test_files[1]['content']))
                }
            ).status_code,
            201
        )

    def test_post_error(self):
        self.assertEqual(
            requests.post(
                self.test_files[0]['dir_url'],
                files={
                    'file_0': (self.test_files[0]['name'], BytesIO(self.test_files[0]['content'])),
                    'file_1': (self.test_files[1]['name'], BytesIO(self.test_files[1]['content'])),
                }
            ).status_code,
            400
        )

    def test_patch_success(self):
        self.test_files[0]['content'] = randbytes(self.DATA_TEST_BYTES_SIZE-1)
        self.test_files[1]['content'] = randbytes(self.DATA_TEST_BYTES_SIZE-1)

        self.assertEqual(
            requests.patch(
                self.test_files[0]['dir_url'],
                files={
                    'file_0': (self.test_files[0]['name'], BytesIO(self.test_files[0]['content'])),
                    'file_1': (self.test_files[1]['name'], BytesIO(self.test_files[1]['content'])),
                    'file_2': (self.test_files[2]['name'], BytesIO(self.test_files[2]['content'])),
                    'file_3': (self.test_files[3]['name'], BytesIO(self.test_files[3]['content']))
                }
            ).status_code,
            200
        )

    def test_patch_error(self):
        self.assertEqual(
            requests.patch(
                self.test_files[0]['dir_url'],
                files={
                    'file_0': (self.test_files[0]['name'], BytesIO(self.test_files[0]['content'])),
                    'file_1': (self.test_files[1]['name'], BytesIO(self.test_files[1]['content'])),
                    'file_2': (self.test_files[2]['name'], BytesIO(self.test_files[2]['content'])),
                    'file_3': (self.test_files[3]['name'], BytesIO(self.test_files[3]['content']))
                }
            ).status_code,
            400
        )

    def test_file_integrity(self):
        for test_file in self.test_files:
            self.assertEqual(test_file.get('download_content', None), test_file['content'])


if __name__ == "__main__":
    loader = TestLoader()
    loader.sortTestMethodsUsing = OSImageRepoTests.order
    suite = loader.loadTestsFromTestCase(OSImageRepoTests)

    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
