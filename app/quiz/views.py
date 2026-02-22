from aiohttp.web import HTTPConflict, HTTPNotFound
from aiohttp_apispec import querystring_schema, request_schema, response_schema
from marshmallow import ValidationError

from app.quiz.schemes import (
    ListQuestionSchema,
    QuestionSchema,
    ThemeIdSchema,
    ThemeListSchema,
    ThemeSchema,
)
from app.web.app import View
from app.web.utils import json_response, error_json_response


class ThemeAddView(View):
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        title = self.data["title"]
        
        existing = await self.store.quizzes.get_theme_by_title(title)
        if existing:
            return error_json_response(
                http_status=409,
                status="conflict",
                message="Theme already exists",
                data={}
            )
        
        theme = await self.store.quizzes.create_theme(title)
        return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(View):
    @response_schema(ThemeListSchema)
    async def get(self):
        themes = await self.store.quizzes.list_themes()
        return json_response(data=ThemeListSchema().dump({"themes": themes}))


class QuestionAddView(View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        try:
            title = self.data["title"]
            theme_id = self.data["theme_id"]
            answers_data = self.data["answers"]
            
            # Проверяем существование темы
            theme = await self.store.quizzes.get_theme_by_id(theme_id)
            if not theme:
                return error_json_response(
                    http_status=404,
                    status="not_found",
                    message="Theme not found",
                    data={}
                )
            
            # Проверяем уникальность вопроса
            existing = await self.store.quizzes.get_question_by_title(title)
            if existing:
                return error_json_response(
                    http_status=409,
                    status="conflict",
                    message="Question already exists",
                    data={}
                )
            
            from app.quiz.models import AnswerModel
            answers = [
                AnswerModel(title=a["title"], is_correct=a["is_correct"]) 
                for a in answers_data
            ]
            
            question = await self.store.quizzes.create_question(title, theme_id, answers)
            return json_response(data=QuestionSchema().dump(question))
            
        except ValidationError as e:
            return error_json_response(
                http_status=400,
                status="bad_request",
                message="Validation error",
                data={"json": e.messages}
            )


class QuestionListView(View):
    @querystring_schema(ThemeIdSchema)
    @response_schema(ListQuestionSchema)
    async def get(self):
        theme_id = self.request.query.get("theme_id")
        if theme_id:
            theme_id = int(theme_id)
        
        questions = await self.store.quizzes.list_questions(theme_id)
        return json_response(data=ListQuestionSchema().dump({"questions": questions}))