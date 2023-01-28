from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()

PUBLIC_URL = ['/', '/group/test-group/', '/profile/auth/', '/posts/1/']
FOR_AUTHORIZED_URL_HTTP_OK = [
    '/create/',
    '/posts/1/edit/',
    '/posts/1/comment/',
]
FOR_AUTHORIZED_URL_HTTP_MOVED_PERMANENTLY = [
    '/profile/following/follow/',
    '/profile/following/unfollow/'
]
TEMPLATES_URL_NAMES = {'/': 'posts/index.html',
                       '/group/test-group/': 'posts/group_list.html',
                       '/posts/1/': 'posts/post_detail.html',
                       '/profile/auth/': 'posts/profile.html',
                       '/create/': 'posts/create_post.html',
                       '/posts/1/edit/': 'posts/create_post.html',
                       '/posts/1/fgfdhdh/': 'core/404.html'
                       }


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.user_followng = User.objects.create_user(username='following')
        cls.user_not_author = User.objects.create_user(username='not-auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_authorized_client_author_get_url(self):
        for url in PUBLIC_URL:
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in FOR_AUTHORIZED_URL_HTTP_OK:
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in FOR_AUTHORIZED_URL_HTTP_MOVED_PERMANENTLY:
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.MOVED_PERMANENTLY)

    def test_authorized_client_not_author_get_url(self):
        response = self.authorized_client_not_author.get(
            FOR_AUTHORIZED_URL_HTTP_OK[1]
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_guest_client_get_url(self):
        for url in PUBLIC_URL:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in FOR_AUTHORIZED_URL_HTTP_OK:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
        for url in FOR_AUTHORIZED_URL_HTTP_MOVED_PERMANENTLY:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_does_not_exist_url(self):
        response = self.guest_client.get('/unexisting-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        for url, template in TEMPLATES_URL_NAMES.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
