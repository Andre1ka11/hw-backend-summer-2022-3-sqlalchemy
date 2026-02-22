from collections.abc import Iterable, Sequence
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from marshmallow import ValidationError

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    AnswerModel,
    QuestionModel,
    ThemeModel,
)


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> ThemeModel:
        async with self.app.database.session() as session:
            theme = ThemeModel(title=title)
            session.add(theme)
            await session.commit()
            await session.refresh(theme)
            return theme

    async def get_theme_by_title(self, title: str) -> Optional[ThemeModel]:
        async with self.app.database.session() as session:
            query = select(ThemeModel).where(ThemeModel.title == title)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_theme_by_id(self, id_: int) -> Optional[ThemeModel]:
        async with self.app.database.session() as session:
            return await session.get(ThemeModel, id_)

    async def list_themes(self) -> Sequence[ThemeModel]:
        async with self.app.database.session() as session:
            query = select(ThemeModel).order_by(ThemeModel.id)
            result = await session.execute(query)
            return result.scalars().all()

    async def create_question(
        self, title: str, theme_id: int, answers: Iterable[AnswerModel]
    ) -> QuestionModel:
        async with self.app.database.session() as session:
            # Проверяем, существует ли тема
            theme = await session.get(ThemeModel, theme_id)
            if not theme:
                raise ValidationError(f"Theme with id {theme_id} not found")
            
            # Проверяем, уникален ли заголовок вопроса
            existing = await self.get_question_by_title(title)
            if existing:
                raise ValidationError(f"Question with title '{title}' already exists")
            
            # Создаем вопрос
            question = QuestionModel(title=title, theme_id=theme_id)
            session.add(question)
            await session.flush()  # Чтобы получить id вопроса
            
            # Создаем ответы
            for answer_data in answers:
                answer = AnswerModel(
                    title=answer_data.title,
                    is_correct=answer_data.is_correct,
                    question_id=question.id,
                )
                session.add(answer)
            
            await session.commit()
            
            # Загружаем вопрос с ответами
            query = select(QuestionModel).where(QuestionModel.id == question.id).options(
                selectinload(QuestionModel.answers)
            )
            result = await session.execute(query)
            return result.scalar_one()

    async def get_question_by_title(self, title: str) -> Optional[QuestionModel]:
        async with self.app.database.session() as session:
            query = select(QuestionModel).where(QuestionModel.title == title).options(
                selectinload(QuestionModel.answers)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def list_questions(
        self, theme_id: Optional[int] = None
    ) -> Sequence[QuestionModel]:
        async with self.app.database.session() as session:
            query = select(QuestionModel).options(selectinload(QuestionModel.answers))
            
            if theme_id is not None:
                query = query.where(QuestionModel.theme_id == theme_id)
            
            query = query.order_by(QuestionModel.id)
            result = await session.execute(query)
            return result.scalars().all()