"""禅道 REST API 客户端"""

import httpx
from typing import Any
from app.config import get_settings

settings = get_settings()


class ZentaoClient:
    """封装禅道 REST API v1 的 HTTP 客户端（支持 Apache 基本认证 + ZenTao Token）"""

    def __init__(self, base_url: str | None = None, account: str | None = None,
                 password: str | None = None, apache_user: str | None = None,
                 apache_pass: str | None = None):
        self.base_url = (base_url or settings.zentao_base_url).rstrip("/")
        self.account = account or settings.zentao_account
        self.password = password or settings.zentao_password
        self.apache_user = apache_user or settings.zentao_apache_auth_user
        self.apache_pass = apache_pass or settings.zentao_apache_auth_pass
        self._token: str | None = None

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api.php/v1"

    @property
    def token(self) -> str:
        if not self._token:
            self._token = self._get_token()
        return self._token

    def _get_token(self) -> str:
        """获取认证 Token（先过 Apache 基本认证）"""
        auth = (self.apache_user, self.apache_pass) if self.apache_user else None
        resp = httpx.post(
            f"{self.api_url}/tokens",
            json={"account": self.account, "password": self.password},
            auth=auth,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token")
        if not token:
            raise Exception(f"获取禅道 Token 失败: {data}")
        return token

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "Token": self.token}

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.api_url}{path}"
        auth = (self.apache_user, self.apache_pass) if self.apache_user else None
        resp = httpx.request(method, url, headers=self._headers(), auth=auth, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ── 产品相关 ──
    def get_products(self) -> list[dict]:
        data = self._request("GET", "/products")
        return data.get("products", [])

    # ── 用例相关 ──
    def get_testcases(self, product_id: int, page: int = 1, limit: int = 100) -> dict:
        return self._request("GET", f"/products/{product_id}/testcases", params={"page": page, "limit": limit})

    def get_testcase(self, testcase_id: int) -> dict:
        return self._request("GET", f"/testcases/{testcase_id}")

    def create_testcase(self, data: dict) -> dict:
        return self._request("POST", "/testcases", json=data)

    def update_testcase(self, testcase_id: int, data: dict) -> dict:
        return self._request("PUT", f"/testcases/{testcase_id}", json=data)

    def write_test_result(self, testcase_id: int, result: dict) -> dict:
        """回写测试结果"""
        return self._request("POST", f"/testcases/{testcase_id}/results", json=result)

    # ── Bug 相关 ──
    def get_bugs(self, product_id: int, page: int = 1, limit: int = 100) -> dict:
        return self._request("GET", f"/products/{product_id}/bugs", params={"page": page, "limit": limit})

    def create_bug(self, data: dict) -> dict:
        """创建 Bug
        data 示例: {"product": 1, "title": "xxx", "severity": 3, "steps": "复现步骤"}
        """
        return self._request("POST", "/bugs", json=data)

    # ── 项目相关 ──
    def get_projects(self) -> list[dict]:
        data = self._request("GET", "/projects")
        return data.get("projects", [])

    # ── 健康检查 ──
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            self._get_token()
            return True
        except Exception:
            return False
