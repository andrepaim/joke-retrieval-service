from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Using pgvector extension
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# Association table for many-to-many relationship between jokes and tags
joke_tags = Table(
    "joke_tags",
    Base.metadata,
    Column("joke_id", Integer, ForeignKey("jokes.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)


class Joke(Base):
    __tablename__ = "jokes"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    source = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=True)  # Using SentenceTransformers default dim
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = relationship("Tag", secondary=joke_tags, back_populates="jokes")
    feedback = relationship("JokeFeedback", back_populates="joke")


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    jokes = relationship("Joke", secondary=joke_tags, back_populates="tags")


class JokeFeedback(Base):
    __tablename__ = "joke_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    joke_id = Column(Integer, ForeignKey("jokes.id"), nullable=False)
    liked = Column(Boolean, nullable=False)
    feedback_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    joke = relationship("Joke", back_populates="feedback")


class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    context = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=True)  # Using SentenceTransformers default dim
    clarification_needed = Column(Boolean, default=False)
    selected_joke_id = Column(Integer, ForeignKey("jokes.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    relevance_score = Column(Float, nullable=True)