from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для всех тестов.
        Создаёт двух пользователей с разными именами и одну заметку, автором
        которой является один из пользователей.
        """

        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='adress',
            author=cls.author,
        )

    def test_pages_availability_for_anywhere(self):
        """
        Проверяет доступность определённых страниц для любого пользователя,
        включая незарегистрированных (анонимных) пользователей.
        """

        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_edit_and_delete_availability(self):
        """
        Проверяет, что доступ к страницам деталей, редактирования и удаления
        заметки имеет только её автор. Для других зарегистрированных
        пользователей доступ запрещён (404 NOT FOUND).
        """

        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:edit', 'notes:delete', 'notes:detail',):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Проверяет, что незарегистрированные пользователи при попытке доступа к
        защищённым страницам перенаправляются на страницу входа с корректным
        параметром 'next'.
        """

        login_url = reverse('users:login')
        for name, arg in [
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
        ]:
            with self.subTest(name=name):
                url = reverse(name, args=arg)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
