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


class CatalogueAndProxyTests(TestCase):
    def test_catalogue_seed_is_repeatable(self):
        from .populate import initiate
        from .models import CarModel
        self.assertEqual(initiate(), (6, 15))
        self.assertEqual(initiate(), (6, 15))
        response = self.client.get('/djangoapp/get_cars')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['CarModels']), 15)
        self.assertIn('Tesla Model 3', [str(car)[:-7] for car in CarModel.objects.all()])

    def test_proxy_state_and_failure(self):
        from unittest.mock import patch
        from .restapis import ServiceError
        with patch('djangoapp.restapis.get_request', return_value=[{'id': 1}]) as upstream:
            response = self.client.get('/djangoapp/get_dealers/Kansas')
            self.assertEqual(response.json()['dealers'], [{'id': 1}])
            upstream.assert_called_once_with('fetchDealers/Kansas')
        with patch('djangoapp.restapis.get_request', side_effect=ServiceError('Unavailable')):
            self.assertEqual(self.client.get('/djangoapp/get_dealers').status_code, 503)

    def test_reviews_get_real_sentiment_result(self):
        from unittest.mock import patch
        with patch('djangoapp.restapis.get_request', return_value=[{'review': 'Excellent!'}]), patch('djangoapp.restapis.analyze_review_sentiments', return_value='positive'):
            response = self.client.get('/djangoapp/reviews/dealer/1')
            self.assertEqual(response.json()['reviews'][0]['sentiment'], 'positive')

    def test_review_requires_session_and_uses_authenticated_identity(self):
        from unittest.mock import patch
        from .populate import initiate
        initiate()
        payload = {'name': 'Spoofed', 'dealership': 1, 'review': 'Great service.',
                   'purchase': True, 'purchase_date': '2023-05-01',
                   'car_make': 'Toyota', 'car_model': 'Camry', 'car_year': 2023}
        self.assertEqual(self.client.post('/djangoapp/add_review', json.dumps(payload), content_type='application/json').status_code, 401)
        user = User.objects.create(username='review_fixture', first_name='Alex')
        self.client.force_login(user)
        with patch('djangoapp.restapis.post_review', return_value={'id': 101}) as post:
            response = self.client.post('/djangoapp/add_review', json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 201)
            self.assertEqual(post.call_args.args[0]['name'], 'Alex')
        payload['car_model'] = 'Not a model'
        self.assertEqual(self.client.post('/djangoapp/add_review', json.dumps(payload), content_type='application/json').status_code, 400)
