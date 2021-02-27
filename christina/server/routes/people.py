from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from christina.db import get_db
from christina.logger import get_logger
from christina.video import crud, schemas

logger = get_logger(__name__)

router = APIRouter(prefix='/people')


@router.get('', response_model=List[schemas.Person])
def route_people(db: Session = Depends(get_db)):
    return crud.get_people(db)
