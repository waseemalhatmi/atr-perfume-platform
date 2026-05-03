# app/utils/validation.py
from functools import wraps
from flask import request, jsonify
from pydantic import BaseModel, ValidationError

class QuizRequestSchema(BaseModel):
    gender: str = "Unisex"
    apparel: str = "Casual"
    activity: str = "Work"
    weather: str = "Moderate"
    vibe: str = "Fresh"
    per_page: int = 5

class SearchRequestSchema(BaseModel):
    q: str = ""
    limit: int = 50

class InteractionSchema(BaseModel):
    target_type: str
    target_id: int

def validate_json(schema: BaseModel):
    """
    Enterprise API Validation Layer (Fix #5 & #11).
    Ensures robust input checking before requests reach business logic.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Try to parse and validate incoming JSON
                data = request.get_json(silent=True) or {}
                validated_data = schema(**data)
                # Inject validated data into kwargs so route can use it safely
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    "success": False,
                    "error": "Validation failed",
                    "details": err.errors(),
                    "code": 400
                }), 400
        return decorated_function
    return decorator

def validate_query(schema: BaseModel):
    """
    Enterprise Query Params Validation Layer.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.args.to_dict()
                validated_data = schema(**data)
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    "success": False,
                    "error": "Invalid query parameters",
                    "details": err.errors(),
                    "code": 400
                }), 400
        return decorated_function
    return decorator
