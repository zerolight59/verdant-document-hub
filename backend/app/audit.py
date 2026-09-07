from typing import Any
from sqlalchemy.orm import Session
from .models import AuditLog

def write_audit(db:Session,actor_id:int|None,action:str,entity_type:str,entity_id:int|None,details:dict[str,Any]|None=None)->None:
    db.add(AuditLog(actor_employee_id=actor_id,action=action,entity_type=entity_type,entity_id=entity_id,details=details))
