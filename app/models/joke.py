from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.database import Base

# Association table for many-to-many relationship between jokes and tags
joke_tags = Table(
    "joke_tags",
    Base.metadata,
    Column("joke_id", Integer, ForeignKey("jokes.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)


class Joke(Base):
    __tablename__ = "jokes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    source = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=True)  # Vector for similarity search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tags = relationship("Tag", secondary=joke_tags, back_populates="jokes")
    feedback = relationship("JokeFeedback", back_populates="joke")

    # Create an index for vector similarity search
    __table_args__ = (
        Index(
            "idx_joke_embedding",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
        ),
    )


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
    embedding = Column(Vector(384), nullable=True)  # Vector for similarity search
    clarification_needed = Column(Boolean, default=False)
    selected_joke_id = Column(Integer, ForeignKey("jokes.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    relevance_score = Column(Float, nullable=True)
