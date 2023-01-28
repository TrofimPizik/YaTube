from django.core.cache import cache
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms


from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.user_follower = User.objects.create_user(username='user_follower')
        cls.user_unfollower = User.objects.create_user(
            username='user_unfollower'
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа-2',
            slug='test-group-2',
            description='Тестовое описание-2',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_author,
        )
        cls.post = []
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        for i in range(12):
            cls.post.append(Post.objects.create(
                            author=cls.user_author,
                            text=f'Тестовый пост{i}',
                            group=cls.group_1,
                            image=uploaded))
        cls.first_post = cls.post[11]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_follower = Client()
        self.authorized_client_unfollower = Client()
        self.authorized_client_author.force_login(self.user_author)
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_unfollower.force_login(self.user_unfollower)

    # Проверяем что URL-адрес использует соответсвующий шаблон
    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-group'}): (
                'posts/group_list.html'),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post[0].id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:profile', kwargs={'username': 'auth'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post[0].id}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем контекст главной страницы
    def test_index_page_show_correct_context(self):
        response = self.authorized_client_author.get(reverse('posts:index'))
        # Проверяем сортировку постов по дате создания
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.id, self.first_post.id)
        # Проверяем контекст поста на главной странице
        self.assertEqual(first_object.text, self.first_post.text)
        self.assertEqual(first_object.author, self.first_post.author)
        self.assertEqual(first_object.group, self.first_post.group)
        self.assertEqual(first_object.image, self.first_post.image)
        # Проверяем количество постов отображаемых на странице
        self.assertEqual(len(response.context['page_obj']), 10)

    # Проверяем контекст страницы группы
    def test_group_list_pages_show_correct_context(self):
        response = self.authorized_client_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group'})
        )
        self.assertEqual(response.context['group'].id,
                         self.group_1.id)
        self.assertEqual(response.context['page_obj'][0].group.id, (
            self.first_post.group.id)
        )
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.first_post.image
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    # Проверяем контекст страницы автора
    def test_profile_pages_show_correct_context(self):
        response = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(response.context['author'].id, (
            self.user_author.id)
        )
        self.assertEqual(response.context['page_obj'][0].author.id, (
            self.first_post.author.id)
        )
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.first_post.image
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    # Проверяем контекст страницы поста
    def test_post_detail_pages_show_correct_context(self):
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post[11].id})
        )
        self.assertEqual(response.context['post'].id, (
            self.first_post.id)
        )
        self.assertEqual(
            response.context['post'].image,
            self.first_post.image
        )

    # Проверяем контекст страницы создания поста
    def test_post_create_show_correct_context(self):
        response = self.authorized_client_author.get(reverse(
            'posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # Проверяем контекст страницы редактирования
    def test_post_edit_show_correct_context(self):
        response = self.authorized_client_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post[0].id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # Проверяем контекст страницы подписок
    def test_follow_index_pages_show_correct_context(self):
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.context['page_obj'][0].group.id, (
            self.first_post.group.id)
        )
        self.assertEqual(response.context['page_obj'][0].author.id,
                         self.user_author.id)
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.first_post.image
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    # Проверяем, что новая запись пользователя не появляется в ленте тех
    # кто на него не подписан
    def test_new_post_in_the_wrong_following(self):
        self.assertNotIn(
            self.post[0],
            self.authorized_client_unfollower.get(
                reverse('posts:follow_index')).context['page_obj']
        )

    # Проверяем, что пост не попал в группу, для которой не был предназначен
    def test_new_post_in_the_wrong_group(self):
        self.assertNotIn(
            self.post[0],
            self.authorized_client_author.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-group-2'})
                                              ).context['page_obj'])

    # Проверяем работу кеша
    def test_cashe_for_main_page(self):
        post_for_cache = Post.objects.create(author=self.user_author,
                                             text='Тестовый пост для кэша',
                                             group=self.group_1,)
        response_1 = self.authorized_client_author.get(reverse('posts:index'))
        post = response_1.content
        post_for_cache.delete()
        response_2 = self.authorized_client_author.get(reverse('posts:index'))
        self.assertEqual(post, response_2.content)
        cache.clear()
        response_3 = self.authorized_client_author.get(reverse('posts:index'))
        self.assertNotEqual(response_3.content, post)
