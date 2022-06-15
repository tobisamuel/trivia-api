import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS"
        )
        return response

    @app.route("/categories")
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        return jsonify({"success": True, "categories": formatted_categories})

    @app.route("/questions")
    def get_paginated_questions():
        questions = Question.query.order_by(Question.id).all()
        paginated_questions = paginate_questions(request, questions)
        categories = {category.id: category.type for category in Category.query.all()}

        if len(questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": paginated_questions,
                "total_questions": len(questions),
                "current_category": None,
                "categories": categories,
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            return jsonify({"success": True})
        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def add_question():
        body = request.get_json()
        question = body.get("question")
        answer = body.get("answer")
        category = body.get("category")
        difficulty = body.get("difficulty")

        try:
            question = Question(
                question=question,
                answer=answer,
                category=category,
                difficulty=difficulty,
            )
            question.insert()
            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "total_questions": len(Question.query.all()),
                }
            )
        except:
            abort(422)

    @app.route("/questions/search", methods=["POST"])
    def search_question():
        body = request.get_json()
        search_term = body.get("searchTerm")

        try:
            result = Question.query.filter(
                Question.question.ilike("%{}%".format(search_term))
            ).all()

            return jsonify(
                {
                    "success": True,
                    "questions": [question.format() for question in result],
                    "total_questions": len(result),
                    "current_category": None,
                }
            )
        except:
            abort(422)

    @app.route("/categories/<int:category_id>/questions")
    def get_questions_by_category(category_id):
        questions = Question.query.filter(Question.category == category_id).all()
        paginated_questions = paginate_questions(request, questions)

        if len(paginated_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": paginated_questions,
                "total_questions": len(questions),
                "current_category": category_id,
            }
        )

    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        body = request.get_json()
        previous_questions = body.get("previous_questions")
        quiz_category = body.get("quiz_category")

        try:
            if quiz_category["id"] == 0:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)
                ).all()
            else:
                questions = Question.query.filter(
                    Question.category == quiz_category["id"],
                    Question.id.notin_(previous_questions),
                ).all()

            if questions:
                question = random.choice(questions)
                return jsonify({"success": True, "question": question.format()})
            else:
                return jsonify({"success": True, "question": None})
        except:
            abort(422)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(500)
    def unprocessable(error):
        return (
            jsonify(
                {"success": False, "error": 500, "message": "internal server error"}
            ),
            500,
        )

    return app
