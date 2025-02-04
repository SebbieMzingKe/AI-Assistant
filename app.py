import json
import datetime as dt
from typing import Union

from pydantic import BaseModel


from fastapi import FastAPI, HTTPException, Depends

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = 'sqlite:///./database.db'

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoFlush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    todo_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.utcnow)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)


class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True, index=True)
    reminder_text = Column(String)
    importance = Column(String)
    