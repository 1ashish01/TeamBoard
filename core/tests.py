from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Company, KBEntry, QueryLog


class TeamBoardAPITests(APITestCase):

    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client_test",
            password="testpass123",
            email="client@test.com"
        )

        self.client_company = self.client_user.company

        self.admin_user = User.objects.create_user(
            username="admin_test_auto",
            password="adminpass123",
            email="admin@test.com"
        )

        self.admin_company = self.admin_user.company
        self.admin_company.role = Company.Role.ADMIN
        self.admin_company.save()

        KBEntry.objects.create(
            question="What is select_related in Django?",
            answer="select_related performs a SQL JOIN.",
            category=KBEntry.Category.DATABASE
        )

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new_company",
                "password": "securepass123",
                "company_name": "New Company",
                "email": "new@test.com"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIn("api_key", response.data)

    def test_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "client_test",
                "password": "testpass123"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("api_key", response.data)

    def test_kb_query_requires_authentication(self):
        response = self.client.post(
            "/api/kb/query/",
            {"search": "select_related"},
            format="json"
        )

        self.assertEqual(response.status_code, 401)

    def test_kb_query(self):
        token = self.get_token(self.client_user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.post(
            "/api/kb/query/",
            {"search": "select_related"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        self.assertEqual(
            QueryLog.objects.filter(
                company=self.client_company
            ).count(),
            1
        )

    def test_blank_search(self):
        token = self.get_token(self.client_user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.post(
            "/api/kb/query/",
            {"search": ""},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_zero_result_query_is_logged(self):
        token = self.get_token(self.client_user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.post(
            "/api/kb/query/",
            {"search": "does_not_exist"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

        log = QueryLog.objects.get(
            company=self.client_company,
            search_term="does_not_exist"
        )

        self.assertEqual(log.results_count, 0)

    def test_admin_usage_summary(self):
        QueryLog.objects.create(
            company=self.client_company,
            search_term="select_related",
            results_count=1
        )

        token = self.get_token(self.admin_user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )
 
        response = self.client.get(
            "/api/admin/usage-summary/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_queries"], 1)
        self.assertEqual(response.data["active_companies"], 1)

    def test_client_cannot_access_admin_summary(self):
        token = self.get_token(self.client_user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.get(
            "/api/admin/usage-summary/"
        )

        self.assertEqual(response.status_code, 403)

    def test_duplicate_username_registration(self):
        response = self.client.post(
        "/api/auth/register/",
        {
            "username": "client_test",
            "password": "securepass123",
            "company_name": "Duplicate Company",
            "email": "duplicate@test.com"
        },
        format="json"
        )

        self.assertEqual(response.status_code, 400)