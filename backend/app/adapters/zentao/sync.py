"""禅道同步服务"""

from sqlalchemy.orm import Session
from app.adapters.zentao.client import ZentaoClient
from app.models.testcase import TestCase
from app.models.execution import Execution
from app.models.zentao import ZentaoSyncLog, SyncType, SyncDirection, SyncStatus


def sync_cases_from_zentao(
    db: Session,
    client: ZentaoClient,
    product_id: int,
    project_id: int,
    user_id: int,
) -> ZentaoSyncLog:
    """从禅道拉取用例到本地"""
    try:
        resp = client.get_testcases(product_id, limit=100)
        cases = resp.get("testcases", [])
        new_count = 0
        update_count = 0

        for zt_case in cases:
            existing = db.query(TestCase).filter(TestCase.zentao_id == zt_case["id"]).first()
            if existing:
                existing.title = zt_case.get("title", existing.title)
                update_count += 1
            else:
                new_tc = TestCase(
                    project_id=project_id,
                    title=zt_case.get("title", ""),
                    description=zt_case.get("steps", ""),
                    zentao_id=zt_case["id"],
                    created_by=user_id,
                )
                db.add(new_tc)
                new_count += 1

        db.commit()

        log = ZentaoSyncLog(
            type=SyncType.CASES_IMPORT,
            direction=SyncDirection.PULL,
            status=SyncStatus.SUCCESS,
            detail=f"从禅道同步用例完成：新增 {new_count} 条，更新 {update_count} 条",
            records_affected=new_count + update_count,
        )
        db.add(log)
        db.commit()
        return log

    except Exception as e:
        log = ZentaoSyncLog(
            type=SyncType.CASES_IMPORT,
            direction=SyncDirection.PULL,
            status=SyncStatus.FAILED,
            detail=f"同步失败: {str(e)}",
        )
        db.add(log)
        db.commit()
        return log


def report_bug_to_zentao(
    db: Session,
    client: ZentaoClient,
    execution: Execution,
    product_id: int,
) -> ZentaoSyncLog:
    """将失败的执行记录上报为禅道 Bug"""
    try:
        bug_data = {
            "product": product_id,
            "title": f"[自动化测试] {execution.error_message or '用例执行失败'}",
            "severity": 3,   # 1-4 严重程度
            "pri": 3,         # 1-4 优先级
            "type": "codeerror",
            "steps": execution.log or "无详细日志",
            "openedBuild": "trunk",
        }
        result = client.create_bug(bug_data)
        bug_id = result.get("id")

        # 记录到执行表
        execution.zentao_bug_id = bug_id
        db.commit()

        log = ZentaoSyncLog(
            type=SyncType.BUG_EXPORT,
            direction=SyncDirection.PUSH,
            status=SyncStatus.SUCCESS,
            detail=f"Bug 上报成功: Bug #{bug_id}",
            records_affected=1,
        )
        db.add(log)
        db.commit()
        return log

    except Exception as e:
        log = ZentaoSyncLog(
            type=SyncType.BUG_EXPORT,
            direction=SyncDirection.PUSH,
            status=SyncStatus.FAILED,
            detail=f"Bug 上报失败: {str(e)}",
        )
        db.add(log)
        db.commit()
        return log


def write_result_to_zentao(
    db: Session,
    client: ZentaoClient,
    execution: Execution,
) -> ZentaoSyncLog:
    """将测试结果回写禅道"""
    try:
        testcase = execution.testcase
        if not testcase or not testcase.zentao_id:
            raise Exception("用例未关联禅道")

        result = "pass" if execution.status.value == "passed" else "fail"
        client.write_test_result(testcase.zentao_id, {
            "result": result,
            "comment": execution.log or "",
        })

        log = ZentaoSyncLog(
            type=SyncType.RESULT_WRITEBACK,
            direction=SyncDirection.PUSH,
            status=SyncStatus.SUCCESS,
            detail=f"结果回写成功: 用例 #{testcase.zentao_id} → {result}",
            records_affected=1,
        )
        db.add(log)
        db.commit()
        return log

    except Exception as e:
        log = ZentaoSyncLog(
            type=SyncType.RESULT_WRITEBACK,
            direction=SyncDirection.PUSH,
            status=SyncStatus.FAILED,
            detail=f"结果回写失败: {str(e)}",
        )
        db.add(log)
        db.commit()
        return log
