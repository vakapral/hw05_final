from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.auth_user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth_user)

        cls.post = Post.objects.create(
            author=cls.auth_user,
            text='Тестовый текст',
            id=42,
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='group-slug',
        )

        cls.public_pages = {
            '/': HTTPStatus.OK,
            '/group/group-slug/': HTTPStatus.OK,
            '/posts/42/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/unexisted_page/': HTTPStatus.NOT_FOUND,
        }

        cls.private_pages = {
            '/create/': HTTPStatus.OK,
            '/posts/42/edit/': HTTPStatus.OK,
            '/unexisted_page/': HTTPStatus.NOT_FOUND,
        }

        cls.templates_url_names = {
            'posts/group_list.html': '/group/group-slug/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': '/posts/42/',
            'posts/create_post.html': '/create/',
            'posts/create_post.html': '/posts/42/edit/',
            'posts/index.html': '/',
            'core/404.html': '/unexisted_page/',
        }

    @classmethod
    def setUp(self) -> None:
        cache.clear()

    def test_public_pages(self):
        """Тест публичных страниц."""
        for page, http_code in self.public_pages.items():
            with self.subTest(http_code=http_code):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, http_code)

    def test_private_pages(self):
        """Тест приватных страниц."""
        for page, http_code in self.private_pages.items():
            with self.subTest(http_code=http_code):
                response = self.auth_client.get(page)
                self.assertEqual(response.status_code, http_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, address in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth_client.get(address)
                self.assertTemplateUsed(response, template)
