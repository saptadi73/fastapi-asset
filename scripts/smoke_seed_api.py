from __future__ import annotations

# ruff: noqa: E402
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.auth.models import AppUser
from app.modules.auth.service import AuthService

DEFAULT_BASE_URL = "http://127.0.0.1:8003"
API_PREFIX = "/api/v1"
RUN_DATE = date(2026, 7, 27)


@dataclass
class StepResult:
    method: str
    path: str
    status_code: int
    ok: bool
    label: str
    request_json: dict[str, Any] | list[Any] | None = None
    query_params: dict[str, Any] | None = None
    response_json: dict[str, Any] | list[Any] | None = None


class SmokeTestError(RuntimeError):
    pass


def require_first(items: list[Any], label: str) -> Any:
    if not items:
        raise SmokeTestError(f"{label} tidak mengembalikan item yang diharapkan.")
    return items[0]


class ApiSmokeRunner:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.results: list[StepResult] = []
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def call(
        self,
        method: str,
        path: str,
        *,
        label: str,
        expected_status: int | tuple[int, ...] = (200, 201),
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if isinstance(expected_status, int):
            expected = (expected_status,)
        else:
            expected = expected_status
        response = await self.client.request(method, path, json=json_body, params=params)
        ok = response.status_code in expected
        self.results.append(
            StepResult(
                method=method.upper(),
                path=path,
                status_code=response.status_code,
                ok=ok,
                label=label,
                request_json=json_body,
                query_params=params,
                )
        )
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise SmokeTestError(
                f"{label} gagal: response bukan JSON ({response.status_code})"
            ) from exc
        if not ok:
            raise SmokeTestError(
                f"{label} gagal dengan status {response.status_code}: "
                f"{json.dumps(payload, ensure_ascii=True)}"
            )
        self.results[-1].response_json = payload
        return payload


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def build_endpoint_samples(results: list[StepResult]) -> list[dict[str, Any]]:
    return [
        {
            "label": item.label,
            "method": item.method,
            "path": item.path,
            "status_code": item.status_code,
            "query_params": item.query_params,
            "request_json": item.request_json,
            "response_json": item.response_json,
        }
        for item in results
    ]


def build_postman_environment(
    *,
    base_url: str,
    login_email: str,
    seed_entities: dict[str, Any],
) -> dict[str, Any]:
    values = [
        {"key": "base_url", "value": base_url, "type": "default", "enabled": True},
        {"key": "api_prefix", "value": API_PREFIX, "type": "default", "enabled": True},
        {"key": "login_email", "value": login_email, "type": "default", "enabled": True},
        {
            "key": "access_token",
            "value": "",
            "type": "secret",
            "enabled": True,
        },
        {
            "key": "refresh_token",
            "value": "",
            "type": "secret",
            "enabled": True,
        },
    ]
    values.extend(
        {
            "key": key,
            "value": str(value),
            "type": "default",
            "enabled": True,
        }
        for key, value in seed_entities.items()
    )
    return {
        "name": f"FastAPI Asset Seed {RUN_DATE.isoformat()}",
        "values": values,
        "_postman_variable_scope": "environment",
        "_postman_exported_at": iso(datetime.now(UTC)),
        "_postman_exported_using": "Codex smoke seed exporter",
    }


def _build_postman_request_item(
    *,
    name: str,
    method: str,
    path: str,
    query_params: dict[str, Any] | None,
    request_json: dict[str, Any] | list[Any] | None,
    include_auth: bool,
) -> dict[str, Any]:
    raw_url = f"{{{{base_url}}}}{path}"
    query: list[dict[str, str]] = []
    if query_params:
        query = [{"key": key, "value": str(value)} for key, value in query_params.items()]
        raw_url = (
            f"{raw_url}?"
            + "&".join(f"{item['key']}={item['value']}" for item in query)
        )
    headers = [{"key": "Content-Type", "value": "application/json"}]
    if include_auth:
        headers.append({"key": "Authorization", "value": "Bearer {{access_token}}"})
    item: dict[str, Any] = {
        "name": name,
        "request": {
            "method": method,
            "header": headers,
            "url": {
                "raw": raw_url,
                "host": ["{{base_url}}"],
                "path": [segment for segment in path.lstrip("/").split("/") if segment],
                "query": query,
            },
        },
    }
    if request_json is not None:
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(request_json, indent=2),
            "options": {"raw": {"language": "json"}},
        }
    return item


def build_postman_collection(
    *,
    base_url: str,
    login_email: str,
    results: list[StepResult],
) -> dict[str, Any]:
    folders: dict[str, list[dict[str, Any]]] = {
        "Authentication": [
            _build_postman_request_item(
                name="Login",
                method="POST",
                path=f"{API_PREFIX}/auth/login",
                query_params=None,
                request_json={
                    "email": login_email,
                    "password": "{{bootstrap_admin_password}}",
                },
                include_auth=False,
            ),
            _build_postman_request_item(
                name="Auth Me",
                method="GET",
                path=f"{API_PREFIX}/auth/me",
                query_params=None,
                request_json=None,
                include_auth=True,
            ),
        ]
    }
    for item in results:
        if item.path.startswith(f"{API_PREFIX}/auth/"):
            continue
        if item.path.startswith(f"{API_PREFIX}/business-partners"):
            folder = "Business Partners"
        elif item.path.startswith(f"{API_PREFIX}/asset-transfers"):
            folder = "Asset Transfers"
        elif item.path.startswith(f"{API_PREFIX}/asset-"):
            folder = "Asset Registry"
        elif item.path.startswith(f"{API_PREFIX}/assets/") or item.path == f"{API_PREFIX}/assets":
            folder = "Asset Registry"
        elif item.path.startswith(f"{API_PREFIX}/tracking"):
            folder = "Tracking"
        elif item.path.startswith(f"{API_PREFIX}/stocktakes"):
            folder = "Stocktake"
        elif item.path.startswith(f"{API_PREFIX}/maintenance"):
            folder = "Maintenance"
        elif item.path.startswith(f"{API_PREFIX}/reports"):
            folder = "Reports"
        else:
            folder = "Misc"
        folders.setdefault(folder, []).append(
            _build_postman_request_item(
                name=item.label,
                method=item.method,
                path=item.path,
                query_params=item.query_params,
                request_json=item.request_json,
                include_auth=True,
            )
        )
    collection_items = [
        {"name": folder_name, "item": requests}
        for folder_name, requests in folders.items()
    ]
    return {
        "info": {
            "name": f"FastAPI Asset API Seed Collection {RUN_DATE.isoformat()}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": (
                "Collection otomatis dari live smoke seed run "
                f"tanggal {RUN_DATE.isoformat()} untuk membantu frontend dan QA."
            ),
        },
        "variable": [
            {"key": "base_url", "value": base_url},
            {"key": "bootstrap_admin_password", "value": ""},
            {"key": "access_token", "value": ""},
        ],
        "item": collection_items,
    }


def build_attachment_payload(
    *,
    entity_type: str,
    entity_id: str,
    category: str,
    title: str,
    created_at: datetime,
) -> dict[str, Any]:
    content = f"{title}:{entity_id}".encode()
    checksum = hashlib.sha256(content).hexdigest()
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "attachment_category": category,
        "title": title,
        "description": f"Attachment smoke test untuk {title}",
        "captured_at": iso(created_at),
        "sequence_no": 1,
        "is_primary": False,
        "visibility": "INTERNAL",
        "source": "UPLOAD",
        "created_at": iso(created_at),
        "file": {
            "original_filename": "smoke-test.txt",
            "display_name": title,
            "file_kind": "DOCUMENT",
            "mime_type": "text/plain",
            "extension": "txt",
            "size_bytes": len(content),
            "checksum_sha256": checksum,
            "storage_provider": "local",
            "storage_bucket": "smoke-tests",
            "storage_object_key": f"smoke/{entity_type.lower()}/{entity_id}.txt",
            "scan_status": "CLEAN",
            "is_encrypted": False,
            "is_active": True,
            "uploaded_at": iso(created_at),
            "metadata": {"source": "smoke-seed-api"},
        },
    }


async def ensure_admin_user(email: str, password: str, full_name: str) -> None:
    async with async_session_factory() as session:
        result = await session.scalar(select(AppUser).where(AppUser.email == email.lower()))
        password_hash = AuthService.hash_password(password)
        if result is None:
            session.add(
                AppUser(
                    email=email.lower(),
                    full_name=full_name,
                    password_hash=password_hash,
                    is_active=True,
                    is_superuser=True,
                    roles=["SUPERUSER"],
                    permissions=["*"],
                )
            )
        else:
            result.full_name = full_name
            result.password_hash = password_hash
            result.is_active = True
            result.is_superuser = True
            result.roles = ["SUPERUSER"]
            result.permissions = ["*"]
        await session.commit()


def start_local_server(base_url: str) -> tuple[subprocess.Popen[str], str]:
    port = base_url.rsplit(":", 1)[-1]
    log_path = REPO_ROOT / "artifacts" / "smoke_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ],
        cwd=str(REPO_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, str(log_path)


async def wait_for_server(base_url: str, timeout_seconds: int = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.monotonic() < deadline:
            try:
                response = await client.get(f"{base_url}{API_PREFIX}/openapi.json")
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
    raise SmokeTestError("Server lokal tidak siap dalam batas waktu tunggu.")


async def login(base_url: str, email: str, password: str) -> tuple[str, dict[str, Any]]:
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            json={"email": email, "password": password},
        )
        payload = response.json()
        if response.status_code != 200:
            raise SmokeTestError(
                "Login smoke test gagal: "
                f"{response.status_code} {json.dumps(payload, ensure_ascii=True)}"
            )
        return payload["data"]["tokens"]["access_token"], payload


async def run_smoke_test(base_url: str) -> dict[str, Any]:
    load_dotenv(REPO_ROOT / ".env")
    admin_email = os.environ["AUTH_BOOTSTRAP_ADMIN_EMAIL"]
    admin_password = os.environ["AUTH_BOOTSTRAP_ADMIN_PASSWORD"]
    admin_full_name = os.environ.get("AUTH_BOOTSTRAP_ADMIN_FULL_NAME", "System Administrator")

    await ensure_admin_user(admin_email, admin_password, admin_full_name)
    token, login_payload = await login(base_url, admin_email, admin_password)
    runner = ApiSmokeRunner(base_url, token)

    suffix = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"
    company_id = str(uuid4())
    branch_id = str(uuid4())
    department_id = str(uuid4())

    try:
        me = await runner.call("GET", f"{API_PREFIX}/auth/me", label="auth me")
        user_id = me["data"]["id"]

        partner = await runner.call(
            "POST",
            f"{API_PREFIX}/business-partners",
            label="create business partner",
            json_body={
                "partner_code": f"BP-{suffix}",
                "partner_name": f"Vendor Smoke {suffix}",
                "email": f"vendor-{suffix}@example.com",
                "phone": "021555000",
                "address": "Jl. Testing No. 1",
                "sap_card_code": f"VND{suffix}",
                "is_active": True,
                "roles": [{"role_type": "SUPPLIER", "valid_from": RUN_DATE.isoformat()}],
            },
        )
        partner_id = partner["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/business-partners", label="list business partners")
        await runner.call(
            "GET",
            f"{API_PREFIX}/business-partners/{partner_id}",
            label="get business partner",
        )

        category = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-categories",
            label="create asset category",
            json_body={
                "category_code": f"CAT-{suffix}",
                "category_name": f"Category Smoke {suffix}",
                "description": "Kategori smoke test",
                "is_active": True,
            },
        )
        category_id = category["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/asset-categories", label="list asset categories")

        asset_class = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-classes",
            label="create asset class",
            json_body={
                "class_code": f"CLS-{suffix}",
                "class_name": f"Class Smoke {suffix}",
                "sap_asset_class_code": f"SAP-{suffix}",
                "default_useful_life_months": 48,
                "is_depreciable": True,
                "is_active": True,
            },
        )
        asset_class_id = asset_class["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/asset-classes", label="list asset classes")

        origin_location = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-locations",
            label="create origin location",
            json_body={
                "location_code": f"LOC-A-{suffix}",
                "location_name": f"Gudang A Smoke {suffix}",
                "location_type": "WAREHOUSE",
                "company_id": company_id,
                "branch_id": branch_id,
                "warehouse_code": f"WHA{suffix[-4:]}",
                "is_active": True,
            },
        )
        origin_location_id = origin_location["data"]["id"]
        destination_location = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-locations",
            label="create destination location",
            json_body={
                "location_code": f"LOC-B-{suffix}",
                "location_name": f"Workshop Smoke {suffix}",
                "location_type": "WORKSHOP",
                "company_id": company_id,
                "branch_id": branch_id,
                "warehouse_code": f"WHB{suffix[-4:]}",
                "is_active": True,
            },
        )
        destination_location_id = destination_location["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/asset-locations", label="list asset locations")

        attribute_definition = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-attribute-definitions",
            label="create asset attribute definition",
            json_body={
                "asset_category_id": category_id,
                "attribute_code": f"POWER-{suffix}",
                "attribute_name": "Rated Power",
                "data_type": "NUMBER",
                "unit_of_measure": "kW",
                "is_required": True,
                "validation_rule": {"min": 1, "max": 500},
            },
        )
        attribute_definition_id = attribute_definition["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/asset-categories/{category_id}/attribute-definitions",
            label="list asset attribute definitions",
        )

        asset = await runner.call(
            "POST",
            f"{API_PREFIX}/assets",
            label="create asset",
            json_body={
                "asset_code": f"AST-{suffix}",
                "asset_name": f"Pompa Smoke {suffix}",
                "description": "Asset smoke test end-to-end",
                "asset_category_id": category_id,
                "asset_class_id": asset_class_id,
                "asset_type": "FIXED_ASSET",
                "asset_status": "IN_SERVICE",
                "condition_status": "GOOD",
                "criticality_level": "HIGH",
                "serial_number": f"SN-{suffix}",
                "manufacturer_id": partner_id,
                "brand": "SmokeBrand",
                "model": "SM-1000",
                "manufacture_year": 2025,
                "company_id": company_id,
                "branch_id": branch_id,
                "current_location_id": origin_location_id,
                "barcode": f"BC-{suffix}",
                "qr_code": f"QR-{suffix}",
                "tag_number": f"TAG-{suffix}",
                "tracking_status": "TRACKED",
                "in_service_date": "2026-07-01",
                "sap_asset_code": f"SAP-AST-{suffix}",
                "sap_item_code": f"ITEM-{suffix}",
            },
        )
        asset_id = asset["data"]["id"]
        tag_number = asset["data"]["tag_number"]
        await runner.call("GET", f"{API_PREFIX}/assets", label="list assets")
        await runner.call("GET", f"{API_PREFIX}/assets/{asset_id}", label="get asset")
        await runner.call(
            "PATCH",
            f"{API_PREFIX}/assets/{asset_id}",
            label="update asset",
            json_body={
                "asset_name": f"Pompa Smoke Updated {suffix}",
                "description": "Asset smoke test updated",
                "condition_status": "FAIR",
                "brand": "SmokeBrandX",
                "model": "SM-2000",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/assets/{asset_id}/attribute-values",
            label="upsert asset attribute value",
            json_body={
                "attribute_definition_id": attribute_definition_id,
                "value_number": 45.5,
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/attribute-values",
            label="list asset attribute values",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/assets/{asset_id}/ownerships",
            label="create asset ownership",
            json_body={
                "owner_type": "PARTNER",
                "owner_partner_id": partner_id,
                "ownership_percentage": 100,
                "effective_from": "2026-07-01",
                "source_reference": "SMOKE-OWNERSHIP",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/ownerships",
            label="list asset ownerships",
        )
        lease_contract = await runner.call(
            "POST",
            f"{API_PREFIX}/lease-contracts",
            label="create lease contract",
            json_body={
                "contract_number": f"LEASE-{suffix}",
                "lessor_partner_id": partner_id,
                "lessee_company_id": company_id,
                "lease_type": "OPERATING_LEASE",
                "accounting_treatment": "EXPENSE_ONLY",
                "start_date": "2026-07-01",
                "end_date": "2026-12-31",
                "extension_option_end_date": "2027-03-31",
                "billing_frequency": "MONTHLY",
                "payment_amount": "2500000",
                "currency_code": "IDR",
                "deposit_amount": "5000000",
                "purchase_option_amount": "10000000",
                "auto_renewal": False,
                "notice_period_days": 30,
                "maintenance_included": True,
                "insurance_included": True,
                "tax_included": False,
                "status": "ACTIVE",
            },
        )
        lease_contract_id = lease_contract["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/lease-contracts",
            label="list lease contracts",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/lease-contracts/{lease_contract_id}",
            label="get lease contract",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/lease-contracts/{lease_contract_id}/assets",
            label="create lease contract asset item",
            json_body={
                "asset_id": asset_id,
                "lease_start_date": "2026-07-01",
                "lease_end_date": "2026-12-31",
                "monthly_amount": "2500000",
                "allocation_percentage": "100",
                "return_condition": "Asset leased untuk skenario smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/lease-contracts/{lease_contract_id}/assets",
            label="list lease contract assets",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/lease-contracts/{lease_contract_id}/payments",
            label="create lease contract payment",
            json_body={
                "period_start": "2026-07-01",
                "period_end": "2026-07-31",
                "due_date": "2026-07-25",
                "principal_amount": "2000000",
                "interest_amount": "250000",
                "service_amount": "150000",
                "tax_amount": "100000",
                "total_amount": "2500000",
                "payment_status": "DUE",
                "sap_ap_invoice_doc_entry": 12001,
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/lease-contracts/{lease_contract_id}/payments",
            label="list lease contract payments",
        )
        assignment = await runner.call(
            "POST",
            f"{API_PREFIX}/assets/{asset_id}/assignments",
            label="create asset assignment",
            json_body={
                "assignment_type": "PRIMARY_CUSTODIAN",
                "employee_id": user_id,
                "department_id": department_id,
                "assigned_at": "2026-07-27T08:00:00Z",
                "assignment_status": "ACTIVE",
                "notes": "Custodian smoke test",
            },
        )
        assignment_id = assignment["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/assignment-history",
            label="get asset assignment history",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/assignments/{assignment_id}/return",
            label="return asset assignment",
            json_body={
                "returned_at": "2026-07-27T08:10:00Z",
                "released_by_employee_at": "2026-07-27T08:10:00Z",
                "notes": "Assignment dikembalikan pada smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/assignment-history",
            label="get asset assignment history after return",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/assets/{asset_id}/status-changes",
            label="create asset status change",
            json_body={
                "new_status": "IDLE",
                "new_condition": "FAIR",
                "effective_at": "2026-07-27T08:15:00Z",
                "reason": "Idle for smoke test",
                "reference_type": "SMOKE",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/status-history",
            label="get asset status history",
        )

        transfer = await runner.call(
            "POST",
            f"{API_PREFIX}/asset-transfers",
            label="create asset transfer",
            json_body={
                "transfer_number": f"TRF-{suffix}",
                "transfer_date": "2026-07-27T09:00:00Z",
                "transfer_type": "INTERNAL",
                "movement_purpose": "RELOCATION",
                "is_permanent": True,
                "from_location_id": origin_location_id,
                "to_location_id": destination_location_id,
                "from_department_id": department_id,
                "to_department_id": department_id,
                "reason": "Relokasi untuk smoke test",
                "items": [
                    {
                        "asset_id": asset_id,
                        "previous_custodian_id": user_id,
                        "new_custodian_id": user_id,
                        "handover_condition": "FAIR",
                        "item_status": "PENDING",
                        "notes": "Transfer smoke test",
                    }
                ],
            },
        )
        transfer_id = transfer["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/asset-transfers", label="list asset transfers")
        await runner.call(
            "GET",
            f"{API_PREFIX}/asset-transfers/{transfer_id}",
            label="get asset transfer",
        )
        action_time = "2026-07-27T09:10:00Z"
        await runner.call(
            "POST",
            f"{API_PREFIX}/asset-transfers/{transfer_id}/submit",
            label="submit asset transfer",
            json_body={"acted_at": action_time, "notes": "Submit smoke"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/asset-transfers/{transfer_id}/approve",
            label="approve asset transfer",
            json_body={"acted_at": "2026-07-27T09:20:00Z", "notes": "Approve smoke"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/asset-transfers/{transfer_id}/complete",
            label="complete asset transfer",
            json_body={"acted_at": "2026-07-27T09:30:00Z", "notes": "Complete smoke"},
        )

        await runner.call(
            "POST",
            f"{API_PREFIX}/assets/{asset_id}/location-changes",
            label="create asset location change",
            json_body={
                "to_location_id": origin_location_id,
                "effective_at": "2026-07-27T09:45:00Z",
                "reason": "Kembali ke lokasi awal untuk tracking smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/location-history",
            label="get asset location history",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/timeline",
            label="get asset timeline",
        )

        await runner.call(
            "POST",
            f"{API_PREFIX}/tracking/scan-events",
            label="create tracking scan event",
            json_body={
                "event_uid": str(uuid4()),
                "raw_tag_uid": tag_number,
                "scan_type": "VERIFY",
                "scan_source": "API",
                "scanned_location_id": origin_location_id,
                "scanned_at": "2026-07-27T10:00:00Z",
                "received_at": "2026-07-27T10:00:10Z",
                "metadata": {"batch": False},
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/tracking/scan-events/batch",
            label="create tracking scan event batch",
            json_body=[
                {
                    "event_uid": str(uuid4()),
                    "raw_tag_uid": tag_number,
                    "scan_type": "CHECK_IN",
                    "scan_source": "API",
                    "scanned_location_id": origin_location_id,
                    "scanned_at": "2026-07-27T10:05:00Z",
                    "received_at": "2026-07-27T10:05:05Z",
                    "metadata": {"batch": True},
                }
            ],
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/tracking",
            label="get asset tracking timeline",
        )

        stocktake = await runner.call(
            "POST",
            f"{API_PREFIX}/stocktakes",
            label="create stocktake session",
            json_body={
                "session_number": f"STK-{suffix}",
                "location_id": origin_location_id,
                "scope_type": "LOCATION",
                "planned_start_at": "2026-07-27T10:30:00Z",
                "planned_end_at": "2026-07-27T11:30:00Z",
                "notes": "Stocktake smoke test",
            },
        )
        stocktake_id = stocktake["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/stocktakes", label="list stocktakes")
        await runner.call(
            "GET",
            f"{API_PREFIX}/stocktakes/{stocktake_id}",
            label="get stocktake session",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/stocktakes/{stocktake_id}/start",
            label="start stocktake session",
            json_body={"acted_at": "2026-07-27T10:31:00Z", "notes": "Start smoke"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/stocktakes/{stocktake_id}/scan",
            label="scan stocktake session",
            json_body={
                "event_uid": str(uuid4()),
                "raw_tag_uid": tag_number,
                "scan_type": "STOCKTAKE",
                "scan_source": "API",
                "scanned_location_id": origin_location_id,
                "scanned_at": "2026-07-27T10:40:00Z",
                "received_at": "2026-07-27T10:40:05Z",
                "metadata": {"stocktake": True},
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/stocktakes/{stocktake_id}/complete",
            label="complete stocktake session",
            json_body={"acted_at": "2026-07-27T11:00:00Z", "notes": "Complete smoke"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/stocktakes/{stocktake_id}/approve",
            label="approve stocktake session",
            json_body={"acted_at": "2026-07-27T11:10:00Z", "notes": "Approve smoke"},
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/reports/location-discrepancies",
            label="get location discrepancies report",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/reports/missing-assets",
            label="get missing assets report",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/reports/unverified-assets",
            label="get unverified assets report",
            params={"days_since_verified": 1},
        )

        priority = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/priorities",
            label="create maintenance priority",
            json_body={
                "code": f"HIGH-{suffix}",
                "name": f"High {suffix}",
                "severity_level": 4,
                "default_response_minutes": 60,
                "default_resolution_minutes": 240,
                "color_code": "#F59E0B",
                "is_emergency": False,
                "is_active": True,
            },
        )
        priority_id = priority["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/priorities",
            label="list maintenance priorities",
        )
        symptom = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/symptom-codes",
            label="create maintenance symptom code",
            json_body={
                "code": f"SYM-{suffix}",
                "name": "Getaran Tinggi",
                "description": "Gejala awal smoke test",
                "is_active": True,
            },
        )
        symptom_id = symptom["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/symptom-codes",
            label="list maintenance symptom codes",
        )
        failure_mode = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/failure-modes",
            label="create maintenance failure mode",
            json_body={
                "code": f"FM-{suffix}",
                "name": "Bearing Failure",
                "description": "Failure mode smoke test",
                "is_active": True,
            },
        )
        failure_mode_id = failure_mode["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/failure-modes",
            label="list maintenance failure modes",
        )
        root_cause = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/root-cause-codes",
            label="create maintenance root cause code",
            json_body={
                "code": f"RCA-{suffix}",
                "name": "Poor Lubrication",
                "description": "Root cause smoke test",
                "is_active": True,
            },
        )
        root_cause_id = root_cause["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/root-cause-codes",
            label="list maintenance root cause codes",
        )

        checklist_template = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/checklist-templates",
            label="create maintenance checklist template",
            json_body={
                "template_code": f"CHK-{suffix}",
                "template_name": f"Checklist Smoke {suffix}",
                "asset_category_id": category_id,
                "maintenance_type": "PREVENTIVE",
                "version_number": 1,
                "effective_from": RUN_DATE.isoformat(),
                "is_active": True,
                "items": [
                    {
                        "sequence_no": 1,
                        "item_code": f"ITEM-{suffix}",
                        "instruction": "Periksa kondisi bearing",
                        "response_type": "PASS_FAIL",
                        "is_required": True,
                        "failure_response_rule": "CREATE_FINDING",
                    }
                ],
            },
        )
        checklist_template_id = checklist_template["data"]["id"]
        checklist_template_detail = await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/checklist-templates/{checklist_template_id}",
            label="get maintenance checklist template",
        )
        checklist_template_item_id = require_first(
            checklist_template_detail["data"]["items"],
            "detail maintenance checklist template",
        )["id"]

        team = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/teams",
            label="create maintenance team",
            json_body={
                "company_id": company_id,
                "team_code": f"TEAM-{suffix}",
                "team_name": f"Team Smoke {suffix}",
                "team_type": "MECHANICAL",
                "department_id": department_id,
                "supervisor_employee_id": user_id,
                "default_location_id": origin_location_id,
                "is_active": True,
            },
        )
        team_id = team["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/maintenance/teams", label="list maintenance teams")
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/teams/{team_id}",
            label="get maintenance team",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/teams/{team_id}/members",
            label="add maintenance team member",
            json_body={
                "employee_id": user_id,
                "member_role": "SUPERVISOR",
                "skill_level": "ADVANCED",
                "effective_from": RUN_DATE.isoformat(),
                "is_primary": True,
            },
        )
        contract = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/contracts",
            label="create maintenance contract",
            json_body={
                "contract_number": f"AMC-{suffix}",
                "contract_name": f"AMC Smoke {suffix}",
                "vendor_partner_id": partner_id,
                "contract_type": "AMC",
                "start_date": "2026-07-01",
                "end_date": "2026-12-31",
                "response_time_hours": "2",
                "resolution_time_hours": "8",
                "preventive_maintenance_included": True,
                "corrective_maintenance_included": True,
                "spare_parts_included": True,
                "labor_included": True,
                "onsite_support_included": True,
                "remote_support_included": True,
                "contract_value": "15000000",
                "currency_code": "IDR",
                "billing_frequency": "MONTHLY",
                "auto_renewal": False,
                "notice_period_days": 30,
                "status": "ACTIVE",
            },
        )
        contract_id = contract["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/contracts",
            label="list maintenance contracts",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/contracts/{contract_id}",
            label="get maintenance contract",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/contracts/{contract_id}/assets",
            label="create maintenance contract asset coverage",
            json_body={
                "asset_id": asset_id,
                "coverage_start_date": "2026-07-01",
                "coverage_end_date": "2026-12-31",
                "coverage_level": "FULL",
                "annual_allocation_amount": "5000000",
                "specific_exclusions": "Tidak termasuk modifikasi design.",
            },
        )
        warranty = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/warranties",
            label="create asset warranty",
            json_body={
                "asset_id": asset_id,
                "warranty_provider_partner_id": partner_id,
                "warranty_type": "MANUFACTURER",
                "warranty_number": f"WAR-{suffix}",
                "coverage_start_date": "2026-07-01",
                "coverage_end_date": "2026-09-30",
                "claim_deadline_date": "2026-10-15",
                "coverage_scope": "Bearing dan motor assembly",
                "status": "ACTIVE",
                "notes": "Warranty smoke test",
            },
        )
        warranty_id = warranty["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/assets/{asset_id}/warranties",
            label="list asset warranties",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/warranties/{warranty_id}",
            label="get asset warranty",
        )

        plan = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/plans",
            label="create maintenance plan",
            json_body={
                "plan_code": f"PLAN-{suffix}",
                "plan_name": f"Plan Smoke {suffix}",
                "asset_category_id": category_id,
                "maintenance_type": "PREVENTIVE",
                "trigger_type": "CALENDAR",
                "calendar_interval_value": 30,
                "calendar_interval_unit": "DAY",
                "default_priority_id": priority_id,
                "default_team_id": team_id,
                "checklist_template_id": checklist_template_id,
                "estimated_duration_minutes": 120,
                "lead_time_days": 3,
                "auto_create_request": False,
                "auto_create_work_order": False,
                "requires_approval": False,
                "effective_from": RUN_DATE.isoformat(),
                "next_due_date": "2026-08-26",
                "is_active": True,
            },
        )
        plan_id = plan["data"]["id"]
        await runner.call("GET", f"{API_PREFIX}/maintenance/plans", label="list maintenance plans")
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/plans/{plan_id}",
            label="get maintenance plan",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/plans/{plan_id}/assets",
            label="add maintenance plan asset",
            json_body={
                "asset_id": asset_id,
                "effective_from": RUN_DATE.isoformat(),
                "is_active": True,
            },
        )
        generated_schedules = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/plans/{plan_id}/generate",
            label="generate maintenance plan schedules",
            json_body={
                "scheduled_start_at": "2026-08-26T01:00:00Z",
                "schedule_prefix": f"SCH{suffix[-4:]}",
                "created_by": user_id,
                "create_work_orders": False,
            },
        )
        schedule_id = require_first(
            generated_schedules["data"],
            "generate maintenance plan schedules",
        )["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/schedules",
            label="list maintenance schedules",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/schedules/{schedule_id}",
            label="get maintenance schedule",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/schedules/{schedule_id}/confirm",
            label="confirm maintenance schedule",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T12:00:00Z"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/schedules/{schedule_id}/reschedule",
            label="reschedule maintenance schedule",
            json_body={
                "actor_id": user_id,
                "scheduled_start_at": "2026-08-27T01:00:00Z",
                "scheduled_end_at": "2026-08-27T03:00:00Z",
                "reschedule_reason": "Penyesuaian smoke test",
            },
        )

        maintenance_request = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests",
            label="create maintenance request",
            json_body={
                "request_number": f"MR-{suffix}",
                "company_id": company_id,
                "asset_id": asset_id,
                "request_type": "BREAKDOWN",
                "source_type": "MANUAL",
                "requested_by_employee_id": user_id,
                "reported_by_name": "Smoke Operator",
                "reported_at": "2026-07-27T12:30:00Z",
                "title": "Pompa bergetar tinggi",
                "problem_description": "Pompa menunjukkan getaran tinggi dan noise.",
                "priority_id": priority_id,
                "asset_location_id": origin_location_id,
                "operating_condition": "RUNNING",
                "is_asset_stopped": False,
                "production_impact": True,
                "created_by": user_id,
                "updated_by": user_id,
            },
        )
        request_id = maintenance_request["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/requests",
            label="list maintenance requests",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/requests/{request_id}",
            label="get maintenance request",
        )
        request_attachment = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests/{request_id}/attachments",
            label="create maintenance request attachment",
            json_body=build_attachment_payload(
                entity_type="MAINTENANCE_REQUEST",
                entity_id=request_id,
                category="OTHER",
                title="Request Smoke Attachment",
                created_at=datetime(2026, 7, 27, 12, 31, tzinfo=UTC),
            ),
        )
        request_attachment_id = request_attachment["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/requests/{request_id}/attachments",
            label="list maintenance request attachments",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/attachments/{request_attachment_id}",
            label="get maintenance request attachment",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/attachments/{request_attachment_id}/download",
            label="get maintenance request attachment download reference",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/attachments/{request_attachment_id}/versions",
            label="list maintenance request attachment versions before upload",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/attachments/{request_attachment_id}/versions",
            label="upload maintenance request attachment new version",
            json_body={
                "original_filename": "smoke-test-v2.txt",
                "display_name": "Request Smoke Attachment v2",
                "mime_type": "text/plain",
                "extension": "txt",
                "size_bytes": 31,
                "checksum_sha256": hashlib.sha256(
                    b"Request Smoke Attachment Version 2"
                ).hexdigest(),
                "storage_bucket": "smoke-tests",
                "storage_object_key": f"smoke/maintenance_request/{request_id}-v2.txt",
                "uploaded_at": "2026-07-27T12:32:00Z",
                "change_notes": "Revisi evidensi request smoke test",
                "metadata": {"source": "smoke-seed-api", "revision": 2},
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/attachments/{request_attachment_id}/versions",
            label="list maintenance request attachment versions",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/attachments/{request_attachment_id}/audit-trail",
            label="get maintenance request attachment audit trail",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests/{request_id}/submit",
            label="submit maintenance request",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T12:35:00Z"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests/{request_id}/triage",
            label="triage maintenance request",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T12:40:00Z",
                "priority_id": priority_id,
                "asset_location_id": origin_location_id,
                "operating_condition": "RUNNING_WITH_VIBRATION",
                "maintenance_contract_id": contract_id,
                "warranty_id": warranty_id,
                "required_response_at": "2026-07-27T13:30:00Z",
                "required_resolution_at": "2026-07-27T18:00:00Z",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/requests/{request_id}/sla-snapshots",
            label="list maintenance request sla snapshots",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests/{request_id}/approve",
            label="approve maintenance request",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T12:45:00Z"},
        )
        skill = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/skills",
            label="create maintenance skill",
            json_body={
                "skill_code": f"BRG-{suffix}",
                "skill_name": "Bearing Replacement",
                "certification_required": True,
            },
        )
        skill_id = skill["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/skills",
            label="list maintenance skills",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/employees/{user_id}/skills",
            label="add employee maintenance skill",
            json_body={
                "maintenance_skill_id": skill_id,
                "proficiency_level": "ADVANCED",
                "certificate_number": f"CERT-{suffix}",
                "valid_from": "2026-01-01",
                "valid_to": "2026-12-31",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/employees/{user_id}/skills",
            label="list employee maintenance skills",
        )
        converted_work_order = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/requests/{request_id}/convert-to-work-order",
            label="convert request to work order",
            json_body={
                "work_order_number": f"WO-{suffix}",
                "maintenance_type": "BREAKDOWN",
                "execution_mode": "HYBRID",
                "scope_of_work": "Investigasi dan perbaikan bearing pompa",
                "planned_start_at": "2026-07-27T13:00:00Z",
                "planned_end_at": "2026-07-27T17:00:00Z",
                "vendor_partner_id": partner_id,
                "requires_shutdown": False,
                "requires_permit": False,
                "requires_verification": True,
                "created_by": user_id,
                "updated_by": user_id,
            },
        )
        work_order_id = converted_work_order["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders",
            label="list maintenance work orders",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}",
            label="get maintenance work order",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/attachments",
            label="create maintenance work order attachment",
            json_body=build_attachment_payload(
                entity_type="MAINTENANCE_WORK_ORDER",
                entity_id=work_order_id,
                category="BEFORE_MAINTENANCE_PHOTO",
                title="WO Smoke Attachment",
                created_at=datetime(2026, 7, 27, 12, 50, tzinfo=UTC),
            ),
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/attachments",
            label="list maintenance work order attachments",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/approve",
            label="approve maintenance work order",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T13:00:00Z"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/required-skills",
            label="create maintenance work order required skill",
            json_body={
                "maintenance_skill_id": skill_id,
                "minimum_proficiency_level": "ADVANCED",
                "certification_required": True,
                "notes": "Skill wajib untuk penggantian bearing smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/required-skills",
            label="list maintenance work order required skills",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/assign",
            label="assign maintenance work order",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T13:05:00Z",
                "employee_id": user_id,
                "assignment_role": "LEAD_TECHNICIAN",
                "planned_minutes": 180,
                "accepted_at": "2026-07-27T13:06:00Z",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/start",
            label="start maintenance work order",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T13:10:00Z"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/hold",
            label="hold maintenance work order",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T13:12:00Z",
                "notes": "Menunggu spare part konfirmasi smoke test",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/resume",
            label="resume maintenance work order",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T13:14:00Z",
                "notes": "Part tersedia, pekerjaan dilanjutkan",
            },
        )
        work_order_part_item_id = str(uuid4())
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/part-requirements",
            label="create maintenance work order part requirement",
            json_body={
                "part_item_id": work_order_part_item_id,
                "required_quantity": "2",
                "reserved_quantity": "1",
                "unit_of_measure": "EA",
                "requirement_status": "PLANNED",
                "is_critical": True,
                "notes": "Bearing replacement untuk corrective maintenance smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/part-requirements",
            label="list maintenance work order part requirements",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/vendor-personnel",
            label="create maintenance work order vendor personnel",
            json_body={
                "vendor_partner_id": partner_id,
                "person_name": "Budi Vendor",
                "contact_phone": "0812-5555-0101",
                "technician_reference": f"VND-{suffix}",
                "check_in_at": "2026-07-27T13:18:00Z",
                "check_out_at": "2026-07-27T15:05:00Z",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/vendor-personnel",
            label="list maintenance work order vendor personnel",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/parts",
            label="create maintenance work order part usage",
            json_body={
                "part_item_id": work_order_part_item_id,
                "quantity": "2",
                "unit_cost": "150000",
                "currency_code": "IDR",
                "usage_type": "REPLACE",
                "used_at": "2026-07-27T13:30:00Z",
                "used_by_employee_id": user_id,
                "serial_number": f"PART-{suffix}",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/labor-logs",
            label="create maintenance work order labor log",
            json_body={
                "employee_id": user_id,
                "started_at": "2026-07-27T13:15:00Z",
                "ended_at": "2026-07-27T15:15:00Z",
                "activity_type": "REPAIR",
                "hourly_rate": "100000",
                "notes": "Perbaikan dan alignment smoke test",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/downtimes",
            label="create maintenance work order downtime",
            json_body={
                "downtime_type": "UNPLANNED",
                "started_at": "2026-07-27T13:20:00Z",
                "ended_at": "2026-07-27T14:50:00Z",
                "reason": "Shutdown pompa untuk inspeksi bearing",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/downtimes",
            label="list maintenance work order downtimes",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/failures",
            label="create maintenance work order failure",
            json_body={
                "failure_number": f"FLR-{suffix}",
                "detected_at": "2026-07-27T13:25:00Z",
                "failure_mode_id": failure_mode_id,
                "symptom_code_id": symptom_id,
                "failure_description": "Bearing macet dan menimbulkan getaran berat.",
                "failure_severity": "HIGH",
                "asset_condition_before": "FAIR",
                "caused_shutdown": True,
                "repeat_failure": True,
                "temporary_action": "Shutdown sementara dan inspeksi cepat.",
                "failure_started_at": "2026-07-27T13:20:00Z",
                "failure_ended_at": "2026-07-27T14:50:00Z",
                "status": "OPEN",
            },
        )
        failure_list = await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/failures",
            label="list maintenance failures",
            params={"work_order_id": work_order_id},
        )
        failure_id = require_first(
            failure_list["data"],
            "list maintenance failures",
        )["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/failures/{failure_id}",
            label="get maintenance failure",
        )
        await runner.call(
            "PATCH",
            f"{API_PREFIX}/maintenance/failures/{failure_id}",
            label="update maintenance failure",
            json_body={
                "root_cause_code_id": root_cause_id,
                "root_cause_description": "Pelumasan bearing tidak memadai.",
                "corrective_action": "Ganti bearing dan tambahkan grease baru.",
                "preventive_action": "Buat inspeksi pelumasan mingguan.",
                "asset_condition_after": "GOOD",
                "status": "CLOSED",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/failures/{failure_id}/attachments",
            label="create maintenance failure attachment",
            json_body=build_attachment_payload(
                entity_type="ASSET_FAILURE",
                entity_id=failure_id,
                category="ROOT_CAUSE_EVIDENCE",
                title="Failure Smoke Attachment",
                created_at=datetime(2026, 7, 27, 15, 20, tzinfo=UTC),
            ),
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/failures/{failure_id}/attachments",
            label="list maintenance failure attachments",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/events",
            label="list maintenance work order events",
        )

        checklist_execution = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/checklists",
            label="start maintenance work order checklist",
            json_body={
                "checklist_template_id": checklist_template_id,
                "performed_by_employee_id": user_id,
                "started_at": "2026-07-27T15:30:00Z",
            },
        )
        checklist_id = checklist_execution["data"]["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/checklists/{checklist_id}",
            label="get maintenance checklist execution",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/checklists/{checklist_id}/results",
            label="submit maintenance checklist results",
            json_body={
                "completed_at": "2026-07-27T15:45:00Z",
                "results": [
                    {
                        "template_item_id": checklist_template_item_id,
                        "boolean_value": False,
                        "performed_at": "2026-07-27T15:40:00Z",
                        "finding_type": "DEFECT",
                        "finding_severity": "HIGH",
                        "finding_description": "Grease housing perlu perbaikan lanjutan.",
                        "recommended_action": "Ganti seal housing.",
                        "requires_follow_up": True,
                        "requires_asset_shutdown": False,
                    }
                ],
            },
        )
        checklist_after_submit = await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/checklists/{checklist_id}",
            label="get maintenance checklist execution after submit",
        )
        first_result = require_first(
            checklist_after_submit["data"]["results"],
            "detail maintenance checklist execution after submit",
        )
        finding_id = require_first(
            first_result["findings"],
            "detail maintenance checklist execution findings",
        )["id"]
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/findings/{finding_id}",
            label="get maintenance finding",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/findings/{finding_id}/attachments",
            label="create maintenance finding attachment",
            json_body=build_attachment_payload(
                entity_type="MAINTENANCE_FINDING",
                entity_id=finding_id,
                category="FINDING_PHOTO",
                title="Finding Smoke Attachment",
                created_at=datetime(2026, 7, 27, 15, 46, tzinfo=UTC),
            ),
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/findings/{finding_id}/attachments",
            label="list maintenance finding attachments",
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/findings/{finding_id}/create-request",
            label="create request from maintenance finding",
            json_body={
                "request_number": f"MRF-{suffix}",
                "priority_id": priority_id,
                "reported_at": "2026-07-27T15:50:00Z",
                "title": "Follow-up dari finding smoke test",
                "problem_description": "Tindak lanjut grease housing dan seal.",
                "requested_vendor_partner_id": partner_id,
                "created_by": user_id,
                "updated_by": user_id,
                "submit": True,
            },
        )

        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/reports/backlog",
            label="get maintenance backlog report",
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/reports/cost",
            label="get maintenance cost report",
            params={"asset_id": asset_id},
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/reports/sla",
            label="get maintenance sla report",
            params={
                "date_from": "2026-07-01T00:00:00+00:00",
                "date_to": "2026-07-27T23:59:59+00:00",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/reports/reliability",
            label="get maintenance reliability report",
            params={
                "date_from": "2026-07-01T00:00:00+00:00",
                "date_to": "2026-07-27T23:59:59+00:00",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/reports/failure-analysis",
            label="get maintenance failure analysis report",
            params={
                "asset_id": asset_id,
                "date_from": "2026-07-01T00:00:00+00:00",
                "date_to": "2026-07-27T23:59:59+00:00",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/assets/{asset_id}/maintenance-history",
            label="get asset maintenance history",
        )

        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/complete",
            label="complete maintenance work order",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T16:00:00Z",
                "completion_summary": "Penggantian bearing selesai.",
                "asset_condition_after": "GOOD",
                "resolution_code": "FIXED",
                "actual_labor_cost": "200000",
                "actual_part_cost": "300000",
                "actual_vendor_cost": "0",
            },
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/verify",
            label="verify maintenance work order",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T16:10:00Z"},
        )
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}/close",
            label="close maintenance work order",
            json_body={"actor_id": user_id, "acted_at": "2026-07-27T16:20:00Z"},
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{work_order_id}",
            label="get maintenance work order final",
        )
        cancellable_work_order = await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders",
            label="create cancellable maintenance work order",
            json_body={
                "work_order_number": f"WOC-{suffix}",
                "company_id": company_id,
                "asset_id": asset_id,
                "maintenance_type": "CORRECTIVE",
                "priority_id": priority_id,
                "title": "WO cancel smoke test",
                "scope_of_work": "Pekerjaan dibatalkan untuk validasi endpoint cancel",
                "execution_mode": "INTERNAL",
                "planned_start_at": "2026-07-28T09:00:00Z",
                "planned_end_at": "2026-07-28T11:00:00Z",
                "requires_shutdown": False,
                "requires_permit": False,
                "requires_verification": False,
                "created_by": user_id,
                "updated_by": user_id,
            },
        )
        cancellable_work_order_id = cancellable_work_order["data"]["id"]
        await runner.call(
            "POST",
            f"{API_PREFIX}/maintenance/work-orders/{cancellable_work_order_id}/cancel",
            label="cancel maintenance work order",
            json_body={
                "actor_id": user_id,
                "acted_at": "2026-07-27T17:20:00Z",
                "notes": "Work order dibatalkan pada smoke test",
            },
        )
        await runner.call(
            "GET",
            f"{API_PREFIX}/maintenance/work-orders/{cancellable_work_order_id}",
            label="get cancelled maintenance work order",
        )
    finally:
        await runner.close()

    artifacts_dir = REPO_ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "seed_smoke_results.json"
    frontend_samples_path = artifacts_dir / "frontend_endpoint_samples.json"
    postman_environment_path = artifacts_dir / "postman_seed_environment.json"
    postman_collection_path = artifacts_dir / "postman_seed_collection.json"
    seed_entities = {
        "run_date_reference": RUN_DATE.isoformat(),
        "auth_user_id": user_id,
        "business_partner_id": partner_id,
        "asset_category_id": category_id,
        "asset_class_id": asset_class_id,
        "origin_location_id": origin_location_id,
        "destination_location_id": destination_location_id,
        "asset_attribute_definition_id": attribute_definition_id,
        "asset_id": asset_id,
        "asset_tag_number": tag_number,
        "asset_assignment_id": assignment_id,
        "asset_transfer_id": transfer_id,
        "stocktake_id": stocktake_id,
        "maintenance_priority_id": priority_id,
        "maintenance_contract_id": contract_id,
        "maintenance_symptom_code_id": symptom_id,
        "maintenance_failure_mode_id": failure_mode_id,
        "maintenance_root_cause_code_id": root_cause_id,
        "asset_warranty_id": warranty_id,
        "maintenance_checklist_template_id": checklist_template_id,
        "maintenance_checklist_template_item_id": checklist_template_item_id,
        "maintenance_team_id": team_id,
        "maintenance_plan_id": plan_id,
        "maintenance_schedule_id": schedule_id,
        "maintenance_request_id": request_id,
        "maintenance_request_attachment_id": request_attachment_id,
        "maintenance_work_order_id": work_order_id,
        "maintenance_cancelled_work_order_id": cancellable_work_order_id,
        "maintenance_failure_id": failure_id,
        "maintenance_checklist_execution_id": checklist_id,
        "maintenance_finding_id": finding_id,
    }
    report_payload = {
        "generated_at": iso(datetime.now(UTC)),
        "run_date_reference": RUN_DATE.isoformat(),
        "base_url": base_url,
        "login_user": login_payload["data"]["user"]["email"],
        "seed_entities": seed_entities,
        "results": [asdict(item) for item in runner.results],
        "summary": {
            "total_steps": len(runner.results),
            "passed_steps": sum(1 for item in runner.results if item.ok),
            "failed_steps": sum(1 for item in runner.results if not item.ok),
        },
    }
    frontend_samples_payload = {
        "generated_at": report_payload["generated_at"],
        "run_date_reference": RUN_DATE.isoformat(),
        "base_url": base_url,
        "seed_entities": seed_entities,
        "endpoint_samples": build_endpoint_samples(runner.results),
        "notes": [
            "Semua sample dihasilkan dari live API run pada Monday, July 27, 2026.",
            "File ini ditujukan untuk frontend agar bisa melihat request dan response nyata.",
            "Gunakan seed_entities untuk mencoba endpoint detail secara manual bila diperlukan.",
        ],
    }
    postman_environment_payload = build_postman_environment(
        base_url=base_url,
        login_email=login_payload["data"]["user"]["email"],
        seed_entities=seed_entities,
    )
    postman_collection_payload = build_postman_collection(
        base_url=base_url,
        login_email=login_payload["data"]["user"]["email"],
        results=runner.results,
    )
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    frontend_samples_path.write_text(
        json.dumps(frontend_samples_payload, indent=2),
        encoding="utf-8",
    )
    postman_environment_path.write_text(
        json.dumps(postman_environment_payload, indent=2),
        encoding="utf-8",
    )
    postman_collection_path.write_text(
        json.dumps(postman_collection_payload, indent=2),
        encoding="utf-8",
    )
    return report_payload


async def async_main() -> int:
    base_url = os.environ.get("SMOKE_BASE_URL", DEFAULT_BASE_URL)
    manage_server = os.environ.get("SMOKE_MANAGE_SERVER", "1") != "0"
    server_process: subprocess.Popen[str] | None = None

    try:
        if manage_server:
            server_process, log_path = start_local_server(base_url)
            print(f"Starting local server for smoke test. Log: {log_path}")
            await wait_for_server(base_url)
        report = await run_smoke_test(base_url)
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    finally:
        if server_process is not None and server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()

    print("Smoke test completed successfully.")
    print(
        json.dumps(
            {
                "base_url": report["base_url"],
                "total_steps": report["summary"]["total_steps"],
                "passed_steps": report["summary"]["passed_steps"],
                "report_path": str(REPO_ROOT / "artifacts" / "seed_smoke_results.json"),
                "frontend_samples_path": str(
                    REPO_ROOT / "artifacts" / "frontend_endpoint_samples.json"
                ),
                "postman_environment_path": str(
                    REPO_ROOT / "artifacts" / "postman_seed_environment.json"
                ),
                "postman_collection_path": str(
                    REPO_ROOT / "artifacts" / "postman_seed_collection.json"
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
