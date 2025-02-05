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
    importance = Column(String) # to be restricted later with an enum


class CalendarEvent(Base):
    __tablename__ = 'calendars'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    event_from = Column(DateTime)
    event_to = Column(DateTime)


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close

# Base models for pydantic
class ToolCallFunction(BaseModel):
    name: str # to know what tool is being called
    arguments: str | dict

class ToolCall(BaseModel):
    id: str
    function: ToolCallFunction

class Message(BaseModel):
    id: str
    toolCalls: list[ToolCall]

class VapiRequest(BaseModel):
    message: Message


class TodoResponse(BaseModel):
    id: int
    title: str
    description: Union[str, None]
    todo_completed: bool
    created_at: DateTime
    updated_at: DateTime

    class Config:
        orm_mode = True


class ReminderResponse(BaseModel):
    id: int
    title: str
    reminder_text: str
    importance: bool

    class Config:
        orm_mode = True

class CalendarEventResponse(BaseModel):
    id: str
    title: str
    description: Union[str, None]
    event_from: dt.datetime
    event_to: dt.datetime

    class Config:
        orm_mode = True

@app.post('/create_todo/')
def create_todo(request: VapiRequest, db: Session = Depends(get_db)):
    for toolcall in request.message.toolCalls:
        if toolcall.function.name == 'createTodo':
            args = toolcall.function.arguments

            break
    else:
        raise HTTPException(status_code=400, detail='Invalid Request')

    if isinstance(args, str):
        args = json.loads(args)

        title = args.get('title', '')
        description = args.get('description', '')

        todo = Todo(title = title, description = description)

        db.add(todo)
        db.commit()
        db.refresh(todo) # if it fails/break try without


        return {
            'results': [
                {
                    'toolCallId': 'toolcall.id',
                    'result': 'success'
                }
            ]
        }


@app.post('/get_todos/')
def get_todos(request: VapiRequest, db: Session = Depends(get_db)):
    for toolcall in request.message.toolCalls:
        if toolcall.function.name == 'getTodos':
            todos = db.query(Todo).all()

            return {
                'results': [
                {
                    'toolCallId': 'toolcall.id',
                    'result': [TodoResponse.from_orm(todo).dict() for todo in todos]
                }
            ]
            }
            
    else:
        raise HTTPException(status_code=400, detail='Invalid Request')


@app.post('/complete_todos/')
def complete_todo(request: VapiRequest, db: Session = Depends(get_db)):
    for toolcall in request.message.toolCalls:
        if toolcall.function.name == 'completeTodo':
            args = toolcall.function.arguments

            break
    else:
        raise HTTPException(status_code=400, detail='Invalid Request')

    if isinstance(args, str):
        args = json.loads(args)

        todo_id = args.get('id')

        if not todo_id:
            raise HTTPException(status_code=400, detail='Missing To-Do ID')

        todo = db.query(Todo).filter(Todo == todo_id).first()

        if not todo:
            raise HTTPException(status_code=404, detail='Todo not found')
        title = args.get('title', '')
        description = args.get('description', '')

        todo = Todo(title = title, description = description)

        todo.todo_completed = True

        
        db.commit()
        db.refresh(todo)

        return {
            'results': [
                {
                    'toolCallId': 'toolcall.id',
                    'result': 'success'
                }
            ]
        }


@app.post('/delete_todo/')
def delete_todo(request: VapiRequest, db: Session = Depends(get_db)):
    for toolcall in request.message.toolCalls:
        if toolcall.function.name == 'completeTodo':
            args = toolcall.function.arguments

            break
    else:
        raise HTTPException(status_code=400, detail='Invalid Request')

    if isinstance(args, str):
        args = json.loads(args)

        todo_id = args.get('id')

        if not todo_id:
            raise HTTPException(status_code=400, detail='Missing To-Do ID')

        todo = db.query(Todo).filter(Todo == todo_id).first()

        if not todo:
            raise HTTPException(status_code=404, detail='Todo not found')
        title = args.get('title', '')
        description = args.get('description', '')

        todo = Todo(title = title, description = description)

        todo.todo_completed = True

        
        db.delete(todo)        
        db.commit()

        return {
            'results': [
                {
                    'toolCallId': 'toolcall.id',
                    'result': 'success'
                }
            ]
        }