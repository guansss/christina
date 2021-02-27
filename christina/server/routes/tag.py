from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from christina.db import get_db
from christina.logger import get_logger
from christina.video import crud, schemas

logger = get_logger(__name__)

router = APIRouter(prefix='/tags')


@router.get('', response_model=List[schemas.Tag])
def route_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)


@router.post('', status_code=201, response_model=schemas.Tag)
def route_add_tag(source: schemas.TagCreate, db: Session = Depends(get_db)):
    db_tag = crud.create_tag(db, name=source.name, alias=source.alias)

    if source.video_id:
        crud.add_video_tag(db, source.video_id, db_tag.id)

    return db_tag


@router.post('/{tag_id}/videos/{video_id}', status_code=200)
def route_add_tag(tag_id: str, video_id: str, db: Session = Depends(get_db)):
    crud.add_video_tag(db, tag_id=tag_id, video_id=video_id)


@router.delete('/{tag_id}/videos/{video_id}', status_code=201)
def route_add_tag(tag_id: str, video_id: str, db: Session = Depends(get_db)):
    crud.remove_video_tag(db, tag_id=tag_id, video_id=video_id)
