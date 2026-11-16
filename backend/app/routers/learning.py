from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, get_optional_user
from ..models import (
    LearningLesson, LearningModule, LearningPath, LearningQuizQuestion,
    User, UserLessonProgress,
)
from ..schemas import LearningExerciseSubmission, LearningQuizSubmission

router = APIRouter(tags=["learning"])
PASSING_SCORE = 70


def _lesson_progress(db: Session, lesson_id: int, user: User | None):
    if user is None:
        return None
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user.id,
        UserLessonProgress.lesson_id == lesson_id,
    ).first()
    if progress is None:
        return {
            "exercise_submitted": False,
            "exercise_response": "",
            "quiz_score": None,
            "quiz_attempts": 0,
            "completed": False,
        }
    return {
        "exercise_submitted": progress.exercise_submitted,
        "exercise_response": progress.exercise_response,
        "quiz_score": progress.quiz_score,
        "quiz_attempts": progress.quiz_attempts,
        "completed": progress.completed_at is not None,
    }


def _path_data(db: Session, path: LearningPath, user: User | None):
    modules = db.query(LearningModule).filter(
        LearningModule.path_id == path.id
    ).order_by(LearningModule.position).all()
    all_lessons = []
    module_data = []
    for module in modules:
        lessons = db.query(LearningLesson).filter(
            LearningLesson.module_id == module.id
        ).order_by(LearningLesson.position).all()
        all_lessons.extend(lessons)
        module_data.append((module, lessons))

    completed_ids = set()
    if user and all_lessons:
        lesson_ids = [lesson.id for lesson in all_lessons]
        completed_ids = {
            lesson_id for (lesson_id,) in db.query(UserLessonProgress.lesson_id).filter(
                UserLessonProgress.user_id == user.id,
                UserLessonProgress.lesson_id.in_(lesson_ids),
                UserLessonProgress.completed_at.is_not(None),
            ).all()
        }

    total_lessons = len(all_lessons)
    completed_count = len(completed_ids)
    modules_result = []
    for module, lessons in module_data:
        modules_result.append({
            "id": module.id,
            "slug": module.slug,
            "title": module.title,
            "description": module.description,
            "position": module.position,
            "lessons": [
                {
                    "id": lesson.id,
                    "slug": lesson.slug,
                    "title": lesson.title,
                    "position": lesson.position,
                    "completed": lesson.id in completed_ids,
                    "progress": _lesson_progress(db, lesson.id, user),
                }
                for lesson in lessons
            ],
        })

    return {
        "id": path.id,
        "slug": path.slug,
        "title": path.title,
        "description": path.description,
        "difficulty": path.difficulty,
        "estimated_minutes": path.estimated_minutes,
        "position": path.position,
        "module_count": len(modules),
        "lesson_count": total_lessons,
        "completed_lessons": completed_count,
        "progress_percent": int(completed_count * 100 / total_lessons) if total_lessons else 0,
        "completed": total_lessons > 0 and completed_count == total_lessons,
        "modules": modules_result,
    }


def _get_path(db: Session, slug: str):
    path = db.query(LearningPath).filter(LearningPath.slug == slug).first()
    if path is None:
        raise HTTPException(404, detail={"detail": "Learning path not found", "code": "not_found"})
    return path


def _get_lesson(db: Session, lesson_id: int):
    lesson = db.query(LearningLesson).filter(LearningLesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(404, detail={"detail": "Lesson not found", "code": "not_found"})
    return lesson


@router.get("/learning-paths")
def list_learning_paths(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    query = db.query(LearningPath).order_by(LearningPath.position, LearningPath.title)
    total = query.count()
    paths = query.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for path in paths:
        data = _path_data(db, path, user)
        data.pop("modules")
        items.append(data)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/learning-paths/{slug}")
def get_learning_path(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return _path_data(db, _get_path(db, slug), user)


@router.get("/learning-lessons/{lesson_id}")
def get_learning_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    lesson = _get_lesson(db, lesson_id)
    module = db.query(LearningModule).filter(LearningModule.id == lesson.module_id).first()
    path = db.query(LearningPath).filter(LearningPath.id == module.path_id).first()
    path_lessons = db.query(LearningLesson).join(
        LearningModule, LearningLesson.module_id == LearningModule.id
    ).filter(LearningModule.path_id == path.id).order_by(
        LearningModule.position, LearningLesson.position
    ).all()
    lesson_index = next(index for index, item in enumerate(path_lessons) if item.id == lesson.id)
    questions = db.query(LearningQuizQuestion).filter(
        LearningQuizQuestion.lesson_id == lesson.id
    ).order_by(LearningQuizQuestion.position).all()
    return {
        "id": lesson.id,
        "slug": lesson.slug,
        "title": lesson.title,
        "position": lesson.position,
        "objectives": lesson.objectives,
        "explanation": lesson.explanation,
        "tutorial_steps": lesson.tutorial_steps,
        "practical_example": lesson.practical_example,
        "code_examples": lesson.code_examples,
        "exercise_prompt": lesson.exercise_prompt,
        "module": {"slug": module.slug, "title": module.title},
        "path": {"slug": path.slug, "title": path.title},
        "previous_lesson_id": path_lessons[lesson_index - 1].id if lesson_index else None,
        "next_lesson_id": path_lessons[lesson_index + 1].id if lesson_index + 1 < len(path_lessons) else None,
        "quiz": [
            {"id": question.id, "question": question.question, "choices": question.choices}
            for question in questions
        ],
        "passing_score": PASSING_SCORE,
        "progress": _lesson_progress(db, lesson.id, user),
    }


@router.put("/learning-lessons/{lesson_id}/exercise")
def submit_learning_exercise(
    lesson_id: int,
    data: LearningExerciseSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = _get_lesson(db, lesson_id)
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user.id,
        UserLessonProgress.lesson_id == lesson.id,
    ).first()
    if progress is None:
        progress = UserLessonProgress(
            user_id=user.id, lesson_id=lesson.id, quiz_attempts=0,
        )
        db.add(progress)
    progress.exercise_response = data.response.strip()
    if not progress.exercise_response:
        raise HTTPException(422, detail={"detail": "Exercise response cannot be blank", "code": "invalid_response"})
    progress.exercise_submitted = True
    if progress.quiz_score is not None and progress.quiz_score >= PASSING_SCORE and progress.completed_at is None:
        progress.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "exercise_submitted": progress.exercise_submitted,
        "completed": progress.completed_at is not None,
        "quiz_score": progress.quiz_score,
    }


@router.post("/learning-lessons/{lesson_id}/quiz")
def submit_learning_quiz(
    lesson_id: int,
    data: LearningQuizSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = _get_lesson(db, lesson_id)
    questions = db.query(LearningQuizQuestion).filter(
        LearningQuizQuestion.lesson_id == lesson.id
    ).order_by(LearningQuizQuestion.position).all()
    if len(data.answers) != len(questions):
        raise HTTPException(422, detail={"detail": "Submit one answer for every quiz question", "code": "invalid_answers"})
    for answer, question in zip(data.answers, questions):
        if answer < 0 or answer >= len(question.choices):
            raise HTTPException(422, detail={"detail": "A quiz answer is out of range", "code": "invalid_answers"})

    correct_count = sum(
        answer == question.correct_option
        for answer, question in zip(data.answers, questions)
    )
    score = int(correct_count * 100 / len(questions)) if questions else 0
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user.id,
        UserLessonProgress.lesson_id == lesson.id,
    ).first()
    if progress is None:
        progress = UserLessonProgress(
            user_id=user.id, lesson_id=lesson.id, quiz_attempts=0,
        )
        db.add(progress)
    progress.quiz_attempts += 1
    progress.quiz_score = max(progress.quiz_score or 0, score)
    if progress.exercise_submitted and progress.quiz_score >= PASSING_SCORE and progress.completed_at is None:
        progress.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "score": score,
        "best_score": progress.quiz_score,
        "passing_score": PASSING_SCORE,
        "passed": score >= PASSING_SCORE,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "completed": progress.completed_at is not None,
    }
