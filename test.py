from unittest import TestCase

from api import app


class APITests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config.update({
            "TESTING": True
        })
        cls.client = app.test_client()
        return super().setUpClass()

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
