"""
Database models and session management using SQLAlchemy.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

from src.core.config import settings

# Create database engine
engine = create_engine(settings.database_url, pool_pre_ping=True, echo=settings.debug)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============= Database Models =============


class MetricsSnapshot(Base):
    """Store raw metrics for each sprint."""

    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    sprint_id = Column(String, unique=True, index=True, nullable=False)
    sprint_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Store all metrics as JSON for flexibility
    metrics_data = Column(JSON, nullable=False)

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MetricsSnapshot(sprint_id='{self.sprint_id}', sprint_name='{self.sprint_name}')>"


class AnalysisReportDB(Base):
    """Store generated retrospective reports."""

    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    sprint_ids = Column(JSON, nullable=False)  # ["SPRINT-123", "SPRINT-124"]

    # Report content
    headline = Column(String, nullable=False)
    summary = Column(Text)
    report_data = Column(JSON, nullable=False)  # Full report as JSON

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    hypotheses = relationship(
        "HypothesisDB", back_populates="report", cascade="all, delete-orphan"
    )
    experiments = relationship(
        "ExperimentDB", back_populates="report", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AnalysisReport(id={self.id}, report_date='{self.report_date}')>"


class HypothesisDB(Base):
    """Store hypotheses with evidence."""

    __tablename__ = "hypotheses"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("analysis_reports.id"), nullable=False)

    hypothesis_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(String, nullable=False)  # High/Medium/Low
    confidence_score = Column(Float, nullable=False)
    potential_impact = Column(Text, nullable=False)
    affected_metrics = Column(JSON, nullable=False)
    supporting_evidence = Column(
        JSON, nullable=False
    )  # List of evidence (evidence_data)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    report = relationship("AnalysisReportDB", back_populates="hypotheses")

    def __repr__(self):
        return f"<Hypothesis(title='{self.title}', confidence='{self.confidence}')>"


class ExperimentDB(Base):
    """Track suggested experiments and their results."""

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("analysis_reports.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    duration_sprints = Column(Integer, default=1)
    implementation_steps = Column(JSON, nullable=False)
    success_metrics = Column(JSON, nullable=False)
    expected_outcome = Column(Text, nullable=False)

    # Experiment status
    status = Column(
        String, default="suggested"
    )  # suggested, in_progress, completed, abandoned

    # Results (filled after completion)
    actual_outcome = Column(Text, nullable=True)
    results_data = Column(JSON, nullable=True)
    was_successful = Column(Boolean, nullable=True)

    # Timestamps
    suggested_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    report = relationship("AnalysisReportDB", back_populates="experiments")

    def __repr__(self):
        return f"<Experiment(title='{self.title}', status='{self.status}')>"


class AnalysisTaskDB(Base):
    """Track async analysis tasks."""

    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)

    status = Column(String, default="pending")  # pending, running, completed, failed
    progress_percent = Column(Integer, default=0)
    message = Column(Text, nullable=True)

    # Request parameters
    sprint_count = Column(Integer, nullable=False)
    focus_metrics = Column(JSON, nullable=True)
    custom_context = Column(Text, nullable=True)

    # Result
    report_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AnalysisTask(task_id='{self.task_id}', status='{self.status}')>"


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (for testing)."""
    Base.metadata.drop_all(bind=engine)
