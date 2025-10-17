"""SQLAlchemy database models for test runs and results."""

from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Run(Base):
    """Represents a test run."""
    __tablename__ = 'runs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    commit_hash = Column(String(40), nullable=False)
    branch = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default='running')  # running, completed, failed
    config = Column(JSON, nullable=True)  # Store additional configuration

    # Relationships
    test_cases = relationship("TestCase", back_populates="run", cascade="all, delete-orphan")


class TestCase(Base):
    """Represents a single test case within a run."""
    __tablename__ = 'test_cases'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey('runs.id'), nullable=False)
    name = Column(String(200), nullable=False)
    command = Column(Text, nullable=False)
    status = Column(String(20), default='pending')  # pending, running, passed, failed
    duration = Column(Float, nullable=True)  # seconds
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Relationships
    run = relationship("Run", back_populates="test_cases")
    results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")
    process_logs = relationship("ProcessLog", back_populates="test_case", cascade="all, delete-orphan")


class TestResult(Base):
    """Represents a check result within a test case."""
    __tablename__ = 'test_results'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    test_case_id = Column(String(36), ForeignKey('test_cases.id'), nullable=False)
    check_name = Column(String(200), nullable=False)
    check_type = Column(String(50), nullable=False)  # simple, llm_judge
    passed = Column(Boolean, nullable=False)
    details = Column(Text, nullable=True)
    artifacts_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_case = relationship("TestCase", back_populates="results")


class ProcessLog(Base):
    """Tracks processes spawned during test execution."""
    __tablename__ = 'process_logs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    test_case_id = Column(String(36), ForeignKey('test_cases.id'), nullable=False)
    pid = Column(Integer, nullable=False)
    command = Column(Text, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout_path = Column(Text, nullable=True)
    stderr_path = Column(Text, nullable=True)

    # Relationships
    test_case = relationship("TestCase", back_populates="process_logs")


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str):
        """Initialize the database manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def create_run(self, commit_hash: str, branch: str, model: str, config: Optional[dict] = None) -> str:
        """Create a new test run.

        Args:
            commit_hash: Git commit hash
            branch: Git branch name
            model: Model being tested
            config: Additional configuration

        Returns:
            Run ID
        """
        session = self.get_session()
        try:
            run = Run(
                commit_hash=commit_hash,
                branch=branch,
                model=model,
                config=config or {}
            )
            session.add(run)
            session.commit()
            return run.id
        finally:
            session.close()

    def complete_run(self, run_id: str, status: str):
        """Mark a run as completed.

        Args:
            run_id: Run ID
            status: Final status (completed or failed)
        """
        session = self.get_session()
        try:
            run = session.query(Run).filter_by(id=run_id).first()
            if run:
                run.end_time = datetime.utcnow()
                run.status = status
                session.commit()
        finally:
            session.close()

    def add_test_case(self, run_id: str, name: str, command: str) -> str:
        """Add a test case to a run.

        Args:
            run_id: Run ID
            name: Test case name
            command: Command to execute

        Returns:
            Test case ID
        """
        session = self.get_session()
        try:
            test_case = TestCase(
                run_id=run_id,
                name=name,
                command=command
            )
            session.add(test_case)
            session.commit()
            return test_case.id
        finally:
            session.close()

    def add_test_result(self, test_case_id: str, check_name: str, check_type: str,
                       passed: bool, details: Optional[str] = None,
                       artifacts_path: Optional[str] = None) -> str:
        """Add a test result to a test case.

        Args:
            test_case_id: Test case ID
            check_name: Name of the check
            check_type: Type of check (simple, llm_judge)
            passed: Whether the check passed
            details: Additional details
            artifacts_path: Path to artifacts

        Returns:
            Test result ID
        """
        session = self.get_session()
        try:
            result = TestResult(
                test_case_id=test_case_id,
                check_name=check_name,
                check_type=check_type,
                passed=passed,
                details=details,
                artifacts_path=artifacts_path
            )
            session.add(result)
            session.commit()
            return result.id
        finally:
            session.close()

    def add_process_log(self, test_case_id: str, pid: int, command: str,
                       stdout_path: Optional[str] = None,
                       stderr_path: Optional[str] = None) -> str:
        """Add a process log entry.

        Args:
            test_case_id: Test case ID
            pid: Process ID
            command: Command executed
            stdout_path: Path to stdout file
            stderr_path: Path to stderr file

        Returns:
            Process log ID
        """
        session = self.get_session()
        try:
            log = ProcessLog(
                test_case_id=test_case_id,
                pid=pid,
                command=command,
                stdout_path=stdout_path,
                stderr_path=stderr_path
            )
            session.add(log)
            session.commit()
            return log.id
        finally:
            session.close()