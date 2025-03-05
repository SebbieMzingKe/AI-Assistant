import json
import datetime as dt
from typing import Union

from pydantic import BaseModel


from fastapi import FastAPI, HTTPException, Depends

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = 'sqlite:///./database.db'

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    todo_completed = Column(Boolean, default=False)
    # created_at = Column(DateTime, default=dt.utcnow)
    # updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)


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
    # created_at: DateTime
    # updated_at: DateTime

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
                    'toolCallId': toolcall.id,
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
                    'toolCallId': toolcall.id,
                    'result': 'success'
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
                    'toolCallId': toolcall.id,
                    'result': 'success'
                }
            ]
        }


@app.post('/delete_todo/')
def delete_todo(request: VapiRequest, db: Session = Depends(get_db)):
    for toolcall in request.message.toolCalls:
        if toolcall.function.name == 'deleteTodo':
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
                    'toolCallId': toolcall.id,
                    'result': 'success'
                }
            ]
        }

# vapi implementation


@app.post('/add_reminder/')
def add_reminder(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'addReminder':
            args = tool_call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            reminder_text = args.get('reminder_text')
            importance = args.get('importance')
            if not reminder_text or not importance:
                raise HTTPException(status_code=400, detail="Missing required fields")
            reminder = Reminder(reminder_text=reminder_text, importance=importance)
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': ReminderResponse.from_orm(reminder).dict()
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")

@app.post('/get_reminders/')
def get_reminders(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'getReminders':
            reminders = db.query(Reminder).all()
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': [ReminderResponse.from_orm(reminder).dict() for reminder in reminders]
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")

@app.post('/delete_reminder/')
def delete_reminder(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'deleteReminder':
            args = tool_call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            reminder_id = args.get('id')
            if not reminder_id:
                raise HTTPException(status_code=400, detail="Missing reminder ID")
            reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if not reminder:
                raise HTTPException(status_code=404, detail="Reminder not found")
            db.delete(reminder)
            db.commit()
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': {'id': reminder_id, 'deleted': True}
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")

@app.post('/add_calendar_entry/')
def add_calendar_entry(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'addCalendarEntry':
            args = tool_call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            title = args.get('title', '')
            description = args.get('description', '')
            event_from_str = args.get('event_from', '')
            event_to_str = args.get('event_to', '')
            
            if not title or not event_from_str or not event_to_str:
                raise HTTPException(status_code=400, detail="Missing required fields")
            
            try:
                event_from = dt.datetime.fromisoformat(event_from_str)
                event_to = dt.datetime.fromisoformat(event_to_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
            
            calendar_event = CalendarEvent(
                title=title,
                description=description,
                event_from=event_from,
                event_to=event_to
            )
            db.add(calendar_event)
            db.commit()
            db.refresh(calendar_event)
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': CalendarEventResponse.from_orm(calendar_event).dict()
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")

@app.post('/get_calendar_entries/')
def get_calendar_entries(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'getCalendarEntries':
            events = db.query(CalendarEvent).all()
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': [CalendarEventResponse.from_orm(event).dict() for event in events]
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")


@app.post('/delete_calendar_entry/')
def delete_calendar_entry(request: VapiRequest, db: Session = Depends(get_db)):
    for tool_call in request.message.toolCalls:
        if tool_call.function.name == 'deleteCalendarEntry':
            args = tool_call.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            event_id = args.get('id')
            if not event_id:
                raise HTTPException(status_code=400, detail="Missing event ID")
            event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if not event:
                raise HTTPException(status_code=404, detail="Calendar event not found")
            db.delete(event)
            db.commit()
            return {
                'results': [{
                    'toolCallId': tool_call.id,
                    'result': {'id': event_id, 'deleted': True}
                }]
            }
    raise HTTPException(status_code=400, detail="Invalid request")