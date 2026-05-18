from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(str(settings.database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema() -> None:
	inspector = inspect(engine)
	tables = set(inspector.get_table_names())

	with engine.begin() as conn:
		if "workflows" in tables:
			workflow_col_defs = inspector.get_columns("workflows")
			workflow_cols = {col["name"] for col in workflow_col_defs}
			workflow_id_type = next(
				(col["type"] for col in workflow_col_defs if col["name"] == "id"), None
			)
			if workflow_id_type and "UUID" not in str(workflow_id_type).upper():
				conn.execute(text("ALTER TABLE workflows ALTER COLUMN id TYPE UUID USING id::uuid"))
			if "description" not in workflow_cols:
				conn.execute(text("ALTER TABLE workflows ADD COLUMN description TEXT"))
			if "status" not in workflow_cols:
				conn.execute(
					text("ALTER TABLE workflows ADD COLUMN status VARCHAR DEFAULT 'pending' NOT NULL")
				)
			if "created_at" not in workflow_cols:
				conn.execute(
					text("ALTER TABLE workflows ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL")
				)
			if "updated_at" not in workflow_cols:
				conn.execute(
					text("ALTER TABLE workflows ADD COLUMN updated_at TIMESTAMP DEFAULT NOW() NOT NULL")
				)

		if "tasks" in tables:
			task_col_defs = inspector.get_columns("tasks")
			task_cols = {col["name"] for col in task_col_defs}
			task_id_type = next(
				(col["type"] for col in task_col_defs if col["name"] == "id"), None
			)
			workflow_id_type = next(
				(col["type"] for col in task_col_defs if col["name"] == "workflow_id"), None
			)
			if task_id_type and "UUID" not in str(task_id_type).upper():
				conn.execute(text("ALTER TABLE tasks ALTER COLUMN id TYPE UUID USING id::uuid"))
			if workflow_id_type and "UUID" not in str(workflow_id_type).upper():
				conn.execute(
					text("ALTER TABLE tasks ALTER COLUMN workflow_id TYPE UUID USING workflow_id::uuid")
				)
			if "title" in task_cols and "name" not in task_cols:
				conn.execute(text("ALTER TABLE tasks RENAME COLUMN title TO name"))
				task_cols.remove("title")
				task_cols.add("name")
			if "name" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN name VARCHAR"))
			if "workflow_id" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN workflow_id UUID"))
			if "description" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN description TEXT"))
			if "status" not in task_cols:
				conn.execute(
					text("ALTER TABLE tasks ADD COLUMN status VARCHAR DEFAULT 'pending' NOT NULL")
				)
			if "agent_name" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN agent_name VARCHAR"))
			if "input_data" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN input_data JSONB"))
			if "output_data" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN output_data JSONB"))
			if "subtasks" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN subtasks JSONB"))
			if "current_agent" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN current_agent VARCHAR"))
			if "agent_output" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN agent_output JSONB"))
			if "test_results" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN test_results JSONB"))
			if "review_results" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN review_results JSONB"))
			if "retry_count" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN retry_count INTEGER DEFAULT 0"))
			if "max_retries" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN max_retries INTEGER DEFAULT 3"))
			if "pipeline_stage" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN pipeline_stage VARCHAR"))
			if "error_log" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN error_log JSONB"))
			if "created_at" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL"))
			if "updated_at" not in task_cols:
				conn.execute(text("ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP DEFAULT NOW() NOT NULL"))

		if "workflow_logs" in tables:
			log_col_defs = inspector.get_columns("workflow_logs")
			log_cols = {col["name"] for col in log_col_defs}
			log_id_type = next((col["type"] for col in log_col_defs if col["name"] == "id"), None)
			log_workflow_id_type = next(
				(col["type"] for col in log_col_defs if col["name"] == "workflow_id"), None
			)
			log_task_id_type = next(
				(col["type"] for col in log_col_defs if col["name"] == "task_id"), None
			)
			if log_id_type and "UUID" not in str(log_id_type).upper():
				conn.execute(text("ALTER TABLE workflow_logs ALTER COLUMN id TYPE UUID USING id::uuid"))
			if log_workflow_id_type and "UUID" not in str(log_workflow_id_type).upper():
				conn.execute(
					text(
						"ALTER TABLE workflow_logs ALTER COLUMN workflow_id TYPE UUID USING workflow_id::uuid"
					)
				)
			if log_task_id_type and "UUID" not in str(log_task_id_type).upper():
				conn.execute(
					text(
						"ALTER TABLE workflow_logs ALTER COLUMN task_id TYPE UUID USING task_id::uuid"
					)
				)
			if "workflow_id" not in log_cols:
				conn.execute(text("ALTER TABLE workflow_logs ADD COLUMN workflow_id UUID"))
			if "task_id" not in log_cols:
				conn.execute(text("ALTER TABLE workflow_logs ADD COLUMN task_id UUID"))
			if "level" not in log_cols:
				conn.execute(
					text("ALTER TABLE workflow_logs ADD COLUMN level VARCHAR DEFAULT 'info' NOT NULL")
				)
			if "agent_name" not in log_cols:
				conn.execute(text("ALTER TABLE workflow_logs ADD COLUMN agent_name VARCHAR"))
			if "pipeline_stage" not in log_cols:
				conn.execute(text("ALTER TABLE workflow_logs ADD COLUMN pipeline_stage VARCHAR"))
			if "created_at" not in log_cols:
				conn.execute(
					text("ALTER TABLE workflow_logs ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL")
				)


def init_db() -> None:
	# Import models to register them with SQLAlchemy metadata.
	from app import models  # noqa: F401

	Base.metadata.create_all(bind=engine)
	ensure_schema()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
