from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from christina.db import get_db
from christina.video import crud, schemas
from christina.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix='/chars')


@router.get('', response_model=List[schemas.Character])
def route_chars(db: Session = Depends(get_db)):
    return crud.get_chars(db)


@router.post('', status_code=201, response_model=schemas.Character)
def route_add_char(source: schemas.CharacterCreate, db: Session = Depends(get_db)):
    db_char = crud.create_char(db, name=source.name, alias=source.alias)

    if source.video_id:
        crud.add_video_char(db, source.video_id, db_char.id)

    return db_char


@router.post('/{char_id}/videos/{video_id}', status_code=200)
def route_add_char(char_id: str, video_id: str, db: Session = Depends(get_db)):
    crud.add_video_char(db, char_id=char_id, video_id=video_id)


@router.delete('/{char_id}/videos/{video_id}')
def route_add_char(char_id: str, video_id: str, db: Session = Depends(get_db)):
    crud.remove_video_char(db, char_id=char_id, video_id=video_id)
