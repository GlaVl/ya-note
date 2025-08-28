from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    """
    Тесты, проверяющие создание заметок.
    """
    @classmethod
    def setUpTestData(cls):
        """
        Подготовка тестовых данных:
        - URL страницы создания заметки,
        - пользователь и авторизованный клиент,
        - данные формы для отправки.
        """
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'title': 'Заголовок', 'text': 'Текст', 'slug': '1'}

    def test_anonymous_user_cant_create_note(self):
        """
    Анонимный пользователь не может создать заметку.
    При попытке POST-запроса количество заметок не увеличивается.
    """

        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_can_create_note(self):
        """
        Проверка, что авторизованный пользователь может успешно создать
        заметку.
        """

        self.auth_client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_cannot_create_note_with_duplicate_slug(self):
        """проверка на то, что нельзя создать две заметки с одинаковым slug"""

        self.auth_client.post(self.url, data=self.form_data)
        count_before = Note.objects.count()
        response = self.auth_client.post(self.url, data=self.form_data)
        count_after = Note.objects.count()
        self.assertEqual(count_before, 1)
        self.assertEqual(count_after, 1)

    def test_slug_auto_generated_if_not_written(self):
        """Если slug не передан, он генерируется через
        pytils.translit.slugify
        """

        data = self.form_data.copy()
        data.pop('slug')
        response = self.auth_client.post(self.url, data=data)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        expected_slug = slugify(data['title'])
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """
    Тесты редактирования и удаления заметок с проверкой прав доступа.
    """

    TITLE = 'Заголовок'
    TEXT = 'Текст'
    SLUG = '1'
    NEW_TITLE = 'Заголовок2'
    NEW_TEXT = 'Текст2'
    NEW_SLUG = '2'

    @classmethod
    def setUpTestData(cls):
        """
        Подготовка тестовых данных:
        - автор заметки и авторизованный клиент,
        - читатель (другой пользователь) и клиент,
        - создание заметки,
        - формирование URL для detail, edit, delete,
        - новые данные формы для редактирования.
        """
        cls.author = User.objects.create(username='Автор поста')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(title=cls.TITLE, text=cls.TEXT,
                                       author=cls.author, slug=cls.SLUG
                                       )
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'title': cls.NEW_TITLE, 'text': cls.NEW_TEXT,
                         'slug': cls.NEW_SLUG
                         }

    def test_author_can_delete_note(self):
        """
        Проверка, что автор заметки может её удалить
        и после удаления происходит редирект на страницу успеха.
        """
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        """
        Проверка, что другой пользователь не может удалить чужую заметку.
        Ожидается 404 и количество заметок не меняется.
        """
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_author_can_edit_note(self):
        """
        Проверка, что автор заметки может её редактировать и получить редирект.
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_TITLE)
        self.assertEqual(self.note.text, self.NEW_TEXT)
        self.assertEqual(self.note.slug, self.NEW_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        """
        Проверка, что другой пользователь не может редактировать чужую заметку.
        Ожидается 404 и данные заметки остаются без изменений.
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.TITLE)
        self.assertEqual(self.note.text, self.TEXT)
        self.assertEqual(self.note.slug, self.SLUG)
