"""测试执行异步任务"""

import logging
from datetime import datetime, timezone
from celery_app.worker import celery_app
from app.database import SessionLocal
from app.models.testplan import TestPlan, PlanStatus
from app.models.testcase import TestCase
from app.models.execution import Execution, ExecutionStatus, TriggerType
from app.models.report import TestReport
from app.engine.browser_agent import run_testcase_sync

logger = logging.getLogger(__name__)


def _build_report(plan: TestPlan, executions: list[Execution]) -> dict:
    """根据执行结果生成测试报告"""
    total = len(executions)
    passed = sum(1 for e in executions if e.status == ExecutionStatus.PASSED)
    failed = sum(1 for e in executions if e.status == ExecutionStatus.FAILED)
    skipped = sum(1 for e in executions if e.status == ExecutionStatus.SKIPPED)
    errors = sum(1 for e in executions if e.status == ExecutionStatus.ERROR)
    pass_rate = (passed / total * 100) if total > 0 else 0

    case_results = []
    for e in executions:
        case_results.append({
            "case_id": e.case_id,
            "status": e.status.value if hasattr(e.status, 'value') else e.status,
            "duration": e.duration or 0,
            "error_message": e.error_message,
            "screenshots": e.screenshots or [],
            "steps": e.steps or [],
        })

    return {
        "plan_id": plan.id,
        "plan_name": plan.name,
        "project_id": plan.project_id,
        "project_name": "",
        "total_count": total,
        "passed_count": passed,
        "failed_count": failed,
        "skipped_count": skipped,
        "error_count": errors,
        "pass_rate": round(pass_rate, 1),
        "duration": sum(e.duration or 0 for e in executions),
        "case_results": case_results,
        "start_time": executions[0].start_time if executions else None,
        "end_time": executions[-1].end_time if executions else None,
    }


@celery_app.task(bind=True)
def execute_plan(self, plan_id: int, trigger_type: str = "manual"):
    """执行整个测试计划中的所有用例"""
    db = SessionLocal()
    try:
        plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            return {"error": "计划不存在"}

        plan.status = PlanStatus.RUNNING
        db.commit()

        case_ids = plan.case_ids or []
        executions = []

        for idx, case_id in enumerate(case_ids):
            # 更新 Celery 任务进度
            self.update_state(
                state="PROGRESS",
                meta={"current": idx + 1, "total": len(case_ids), "case_id": case_id},
            )

            tc = db.query(TestCase).filter(TestCase.id == case_id).first()
            if not tc:
                continue

            # 创建执行记录
            execution = Execution(
                plan_id=plan.id,
                case_id=case_id,
                status=ExecutionStatus.RUNNING,
                trigger_type=TriggerType.MANUAL if trigger_type == "manual" else TriggerType.CRON,
                start_time=datetime.now(timezone.utc),
                executed_by=trigger_type,
            )
            db.add(execution)
            db.commit()

            try:
                # 执行用例
                step_results = run_testcase_sync(tc, execution)
                end_time = datetime.now(timezone.utc)
                duration = (end_time - execution.start_time).total_seconds() * 1000

                all_passed = all(s.get("status") == "passed" for s in step_results)

                execution.status = ExecutionStatus.PASSED if all_passed else ExecutionStatus.FAILED
                execution.steps = step_results
                execution.duration = duration
                execution.end_time = end_time
                execution.log = "\n".join(
                    f"步骤 {s['seq']}: {s['action']} - {s['status']}"
                    for s in step_results
                )

            except Exception as e:
                execution.status = ExecutionStatus.ERROR
                execution.error_message = str(e)
                execution.end_time = datetime.now(timezone.utc)
                execution.log = f"执行异常: {str(e)}"

            db.commit()
            executions.append(execution)

        # 生成测试报告
        report_data = _build_report(plan, executions)
        report = TestReport(
            plan_id=plan.id,
            plan_name=plan.name,
            project_id=plan.project_id,
            project_name=report_data["project_name"],
            total_count=report_data["total_count"],
            passed_count=report_data["passed_count"],
            failed_count=report_data["failed_count"],
            skipped_count=report_data["skipped_count"],
            error_count=report_data["error_count"],
            pass_rate=report_data["pass_rate"],
            duration=report_data["duration"],
            case_results=report_data["case_results"],
            start_time=report_data["start_time"] or datetime.now(timezone.utc),
            end_time=report_data["end_time"] or datetime.now(timezone.utc),
        )
        db.add(report)

        plan.status = PlanStatus.COMPLETED
        db.commit()

        return {
            "plan_id": plan.id,
            "total": report_data["total_count"],
            "passed": report_data["passed_count"],
            "failed": report_data["failed_count"],
            "pass_rate": report_data["pass_rate"],
            "report_id": report.id,
        }

    except Exception as e:
        logger.error(f"执行计划 {plan_id} 失败: {e}")
        plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if plan:
            plan.status = PlanStatus.COMPLETED
            db.commit()
        return {"error": str(e)}

    finally:
        db.close()
