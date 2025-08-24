from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestListPage(TestCase):
    """
    Тестовый класс для проверки страницы списка заметок.
    """

    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        """
        Создание тестовых данных: автора и трех заметок.
        """

        cls.author = User.objects.create(username='Автор')
        for index in range(1, 4):
            note = Note(
                title=f'Заголовок {index}',
                text='Просто текст.',
                author=cls.author,
            )
            note.save()

    def test_notes_order(self):
        """
        Проверка, что заметки на странице упорядочены по возрастанию ID.
        """

        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context["note_list"]
        all_notes = [note.id for note in object_list]
        sorted_notes = sorted(all_notes)
        self.assertEqual(all_notes, sorted_notes)


class TestAddPage(TestCase):
    """
    Тестовый класс для проверки страницы добавления заметки.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Создание тестовых данных: пользователь и URL страницы добавления заметки.
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
