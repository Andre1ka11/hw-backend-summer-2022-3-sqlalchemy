from typing import TYPE_CHECKING

from app.store.admin.accessor import AdminAccessor
from app.store.quiz.accessor import QuizAccessor

if TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        self.app = app
        self.admins = AdminAccessor(app)
        self.quizzes = QuizAccessor(app)


def setup_store(app: "Application"):
    app.store = Store(app)
