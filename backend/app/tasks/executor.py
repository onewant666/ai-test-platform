"""测试执行 Celery 任务"""

import json
import logging
from datetime import datetime

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.execution import Execution, ExecutionStatus
from app.models.testcase import TestCase
from app.models.testplan import TestPlan, PlanStatus
from app.engine.browser_agent import execute_testcase
from app.api.v1.ws import broadcast_execution_update

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_testcase_execution(self, execution_id: int):
    """
    异步执行单个用例的 AI 浏览器测试。
    该任务由 run_plan 触发。
    """
    db = SessionLocal()
    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return {"status": "error", "error": "Execution not found"}

        tc = db.query(TestCase).filter(TestCase.id == execution.case_id).first()
        if not tc:
            logger.error(f"TestCase {execution.case_id} not found")
            execution.status = ExecutionStatus.ERROR
            execution.error_message = "用例不存在"
            db.commit()
            return {"status": "error", "error": "TestCase not found"}

        # 更新状态为 running
        execution.status = ExecutionStatus.RUNNING
        execution.start_time = datetime.utcnow()
        db.commit()

        # WebSocket 推送
        try:
            loop = __import__("asyncio").new_event_loop()
            loop.run_until_complete(
                broadcast_execution_update(execution_id, {
                    "event": "status_change",
                    "execution_id": execution_id,
                    "case_id": tc.id,
                    "case_title": tc.title,
                    "status": "running",
                    "message": f"开始执行: {tc.title}",
                })
            )
        except Exception:
            pass

        # 执行 AI 浏览器测试
        try:
            steps_results = execute_testcase(tc, execution)

            # 更新执行结果
            execution.steps = steps_results
            execution.status = ExecutionStatus.PASSED
            execution.end_time = datetime.utcnow()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds() * 1000
            execution.log = _build_log(steps_results)

        except Exception as exec_err:
            logger.error(f"Browser execution failed for execution {execution_id}: {exec_err}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(exec_err)[:1000]
            execution.end_time = datetime.utcnow()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds() * 1000
            execution.log = str(exec_err)

        db.commit()

        # 检查计划是否全部完成
        _check_plan_completion(db, execution.plan_id)

        # WebSocket 推送最终状态
        try:
            import asyncio as _asyncio2
            loop = _asyncio2.new_event_loop()
            loop.run_until_complete(
                broadcast_execution_update(execution_id, {
                    "event": "status_change",
                    "execution_id": execution_id,
                    "case_id": tc.id,
                    "case_title": tc.title,
                    "status": execution.status.value if hasattr(execution.status, 'value') else execution.status,
                    "message": f"执行完成: {tc.title} → {execution.status.value}",
                    "duration": execution.duration,
                })
            )
        except Exception:
            pass

        return {
            "execution_id": execution_id,
            "status": execution.status.value if hasattr(execution.status, 'value') else execution.status,
        }

    except Exception as e:
        logger.error(f"Task error for execution {execution_id}: {e}")
        try:
            self.retry(exc=e)
        except Exception:
            return {"status": "error", "error": str(e)}
    finally:
        db.close()


def _build_log(steps_results: list[dict]) -> str:
    """构建执行日志"""
    lines = []
    for step in steps_results:
        status = step.get("status", "?")
        action = step.get("action", "")
        icon = {"passed": "✓", "failed": "✗", "skipped": "○"}.get(status, "?")
        lines.append(f"[{icon}] 步骤 {step.get('seq', '?')}: {action} ({status})")
    return "\n".join(lines)


def _check_plan_completion(db, plan_id: int):
    """检查计划下所有执行是否完成，更新计划状态"""
    from sqlalchemy import and_

    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    if not plan:
        return

    total = db.query(Execution).filter(Execution.plan_id == plan_id).count()
    finished = db.query(Execution).filter(
        and_(
            Execution.plan_id == plan_id,
            Execution.status.in_([
                ExecutionStatus.PASSED,
                ExecutionStatus.FAILED,
                ExecutionStatus.ERROR,
                ExecutionStatus.SKIPPED,
            ])
        )
    ).count()

    if total > 0 and finished >= total:
        plan.status = PlanStatus.COMPLETED
        db.commit()
        logger.info(f"Plan {plan_id} completed: {finished}/{total} executions done")
