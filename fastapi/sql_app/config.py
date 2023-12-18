# app/config.py

import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str = Field('postgresql://evanagovino@db:5432/album_data')

settings = Settings()
