"""Authentication regression tests use an isolated, disposable test database."""
import json
from django.contrib.auth.models import User
from django.test import Client, TestCase


class AuthenticationTests(TestCase):
    def setUp(self):
        self.payload = {'userName': 'fixture_user', 'firstName': 'Alex',
                        'lastName': 'Example', 'email': 'fixture@example.com',
                        'password': 'Ephemeral-Test-Only-8294!'}

    def post(self, path, data):
        return self.client.post('/djangoapp/' + path,
                                json.dumps(data), content_type='application/json')

    def test_signup_login_logout(self):
        response = self.post('register', self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['userName'], 'fixture_user')
        self.assertTrue(User.objects.get(username='fixture_user').check_password(
            self.payload['password']))
        self.assertEqual(self.client.get('/djangoapp/session').json()['status'],
                         'Authenticated')
        self.assertEqual(self.post('logout', {}).status_code, 200)
        self.assertEqual(self.client.get('/djangoapp/session').json()['status'],
                         'Anonymous')
        self.assertEqual(self.post('login', self.payload).status_code, 200)

    def test_duplicate_does_not_overwrite_account(self):
        self.assertEqual(self.post('register', self.payload).status_code, 201)
        self.assertEqual(self.post('register', self.payload).status_code, 409)
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_weak_password_and_invalid_email(self):
        self.assertEqual(self.post('register', {**self.payload,
                                              'password': '123'}).status_code, 400)
        self.assertEqual(self.post('register', {**self.payload,
                                              'email': 'invalid'}).status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_rejects_invalid_json_and_credentials(self):
        self.assertEqual(self.post('login', []).status_code, 400)
        self.assertEqual(self.post('login', self.payload).status_code, 401)
        self.assertEqual(self.client.get('/djangoapp/logout').status_code, 405)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/djangoapp/register', json.dumps(self.payload),
                                     content_type='application/json').status_code, 403)
        client.get('/djangoapp/session')
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/djangoapp/register', json.dumps(self.payload),
                                     content_type='application/json',
                                     HTTP_X_CSRFTOKEN=token).status_code, 201)
