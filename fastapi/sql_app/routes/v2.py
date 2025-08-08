from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ._utils import pull_relevant_albums_new, unpack_albums
import numpy as np
import json

router = APIRouter(prefix="/v2", tags=["v2"])

@router.get("/get_relevant_albums/", response_model=schemas.AlbumsList)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] =Query([None]), 
                        list: List[str] = Query([None]), 
                        points_weight: float = 0.5,
                        randomize: bool = False,
                        order_by_recency: bool = False,
                        album_limit: int = 50,
                        db: Session = Depends(get_db)
                        ):
    """
    Return a list of relevant albums given a set of inputs

    Returned in list format, used for Flutterflow
    """
    x = pull_relevant_albums_new(db=db, 
                                 min_year=min_year,
                                 max_year=max_year, 
                                 genre=genre, 
                                 subgenre=subgenre, 
                                 publication=publication, 
                                 list=list,
                                 points_weight=points_weight,
                                 album_uri_required=False
                                 )
    new_dict = []
    if order_by_recency:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['album_key'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    else:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    x['albums'] = new_dict
    return x