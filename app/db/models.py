from pydantic import BaseModel, Field, RootModel
from pydantic_core import CoreSchema
from pydantic import GetJsonSchemaHandler
from bson import ObjectId
from typing import List, Any, Dict

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(ObjectId),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

class PointOfDiscussion(RootModel):
    root: List[str]

class ListTopic(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    main_topic_id: PyObjectId
    topic_name: str
    objective: str
    key_concepts: str
    skills_to_be_mastered: str
    point_of_discussion: PointOfDiscussion

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MainTopic(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    main_topic: str
    cost: float
    list_of_topics: List[str]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
