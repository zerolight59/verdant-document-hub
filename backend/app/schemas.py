from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from .models import AccessLevel, RequirementStatus, ReviewDecision

class ORMModel(BaseModel): model_config=ConfigDict(from_attributes=True)
class LoginRequest(BaseModel): employee_code:str; password:str
class EmployeeOut(ORMModel): id:int; employee_code:str; name:str; email:str; job_title:str; is_admin:bool
class TokenOut(BaseModel): access_token:str; token_type:str="bearer"; employee:EmployeeOut
class ProjectCreate(BaseModel): name:str=Field(min_length=2,max_length=180); description:str|None=None; lifecycle_template_id:int|None=None
class ProjectOut(ORMModel): id:int; name:str; description:str|None; owner_id:int; lifecycle_template_id:int|None; created_at:datetime
class MemberCreate(BaseModel): employee_id:int; access_level:AccessLevel=AccessLevel.VIEW
class StageCreate(BaseModel): name:str=Field(min_length=1,max_length=120); position:int=Field(ge=1)
class RequirementCreate(BaseModel): stage_id:int; document_type_name:str=Field(min_length=1,max_length=180); title:str=Field(min_length=1,max_length=220); description:str|None=None; responsible_employee_id:int|None=None; reviewer_employee_id:int|None=None; due_date:date|None=None
class RequirementAssign(BaseModel): responsible_employee_id:int|None=None; reviewer_employee_id:int|None=None
class DocumentPermissionIn(BaseModel): employee_id:int; access_level:AccessLevel
class ReviewDecisionIn(BaseModel): decision:ReviewDecision; comment:str|None=None
class CategoryCreate(BaseModel): name:str=Field(min_length=1,max_length=180); parent_id:int|None=None
class LinkResearch(BaseModel): project_id:int
class EndorseResearch(BaseModel): label:str=Field(default="Endorsed",max_length=100)
class SearchResult(BaseModel): kind:str; id:int; title:str; context:str; status:str|None=None
class MessageOut(BaseModel): message:str

