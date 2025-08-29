from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestListPage(TestCase):
    """
    Тестовый класс для проверки страницы списка заметок.
    """
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        """
        Создает тестовых пользователей и заметки:
         - автор
         - три заметки автора
         - другой пользователь и его заметка
        """
        cls.author = User.objects.create(username='Автор')
        for index in range(1, 4):
            Note.objects.create(
                title=f'Заголовок {index}',
                text='Просто текст.',
                author=cls.author,
            )
        cls.other_user = User.objects.create(username='Другой')
        Note.objects.create(
            title='Другой заголовок',
            text='Текст другого пользователя',
            author=cls.other_user,
        )

    def test_notes_order(self):
        """
        Проверяет, что на странице списка заметок заметки отсортированы
        по возрастанию ID.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context["note_list"]
        all_notes = [note.id for note in object_list]
        sorted_notes = sorted(all_notes)
        self.assertEqual(all_notes, sorted_notes)

    def test_note_in_context_is_created_note(self):
        """
        Проверяет, что на страницу списка заметок в контекст передается
        хотя бы одна из созданных тестовых заметок (по заголовку).
        """

        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        notes_titles = [note.title for note in response.context['note_list']]
        self.assertIn('Заголовок 1', notes_titles)

    def test_notes_of_other_user_are_not_in_list(self):
        """Проверка, что заметки другого пользователя не попадают в список"""

        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        notes_authors = [note.author for note in response.context['note_list']]
        self.assertNotIn(self.other_user, notes_authors)


class TestAddPage(TestCase):
    """
    Тестовый класс для проверки страницы добавления заметки.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Создание тестовых данных: пользователь и URL страницы
        добавления заметки.
        """

        cls.author = User.objects.create(username='Пользователь')
        cls.add_url = reverse("notes:add")

    def test_anonymous_client_has_no_form(self):
        """
        Проверка, что анонимный клиент при запросе страницы добавления
        получает редирект, и контекст отсутствует.
        """

        response = self.client.get(self.add_url)
        self.assertIsNone(response.context)

    def test_authorized_client_has_form(self):
        """
        Проверка, что авторизованный клиент при запросе страницы добавления
        получает форму в контексте и она соответствует классу NoteForm.
        """

        self.client.force_login(self.author)
        response = self.client.get(self.add_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
