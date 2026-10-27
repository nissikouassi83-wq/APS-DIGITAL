from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="dashboard-viewer",
            password="Secure-test-password-2026",
        )

    def test_dashboard_redirects_anonymous_visitors_to_login(self):
        response = self.client.get(reverse("index"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('index')}",
        )

    def test_login_page_is_available_without_authentication(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion au tableau de bord")

    def test_authenticated_user_can_open_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_post_and_ends_the_session(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("index"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('index')}",
        )

    def test_password_change_requires_authentication(self):
        response = self.client.get(reverse("password_change"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('password_change')}",
        )

    def test_authenticated_user_can_open_password_change_form(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Changer le mot de passe")
