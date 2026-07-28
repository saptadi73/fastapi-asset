# Frontend Page Endpoint Map

Dokumen ini adalah panduan cepat untuk tim frontend agar setiap halaman punya:

- endpoint utama yang perlu dipanggil;
- endpoint pendukung untuk filter, tab, atau action;
- seed entity yang bisa langsung dipakai untuk uji manual;
- artefak sample response yang relevan.

Semua contoh mengacu pada live seed run tanggal **Tuesday, July 28, 2026**.

## Referensi Cepat

Artefak yang dipakai bersama dokumen ini:

- `artifacts/frontend_endpoint_samples.json`
- `artifacts/seed_smoke_results.json`
- `artifacts/postman_seed_environment.json`
- `docs/api/frontend-seed-scenarios.md`

## Global Setup

Sebelum membuka halaman bisnis:

1. `POST /api/v1/auth/login`
2. `GET /api/v1/auth/me`

Kebutuhan frontend:

- simpan `access_token`
- simpan `refresh_token`
- pakai `Authorization: Bearer <token>`

Seed entity yang relevan:

- `auth_user_id`

## Asset List

Tujuan data:

- tabel asset utama;
- filter category, class, dan location;
- navigasi ke asset detail.

Endpoint utama:

- `GET /api/v1/assets`

Endpoint pendukung:

- `GET /api/v1/asset-categories`
- `GET /api/v1/asset-classes`
- `GET /api/v1/asset-locations`

Seed entity untuk drilldown:

- `asset_id`
- `asset_category_id`
- `asset_class_id`
- `origin_location_id`

Sample yang sebaiknya dibuka:

- `list assets`
- `list asset categories`
- `list asset classes`
- `list asset locations`

## Asset Detail

Tujuan data:

- ringkasan master asset;
- tab attribute, ownership, assignment, components, lifecycle, status, location,
  tracking, timeline, maintenance.

Endpoint utama:

- `GET /api/v1/assets/{asset_id}`

Endpoint tab:

- `GET /api/v1/assets/{asset_id}/attribute-values`
- `GET /api/v1/assets/{asset_id}/ownerships`
- `GET /api/v1/assets/{asset_id}/assignment-history`
- `GET /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/component-history`
- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`
- `GET /api/v1/assets/{asset_id}/retirement-requests`
- `GET /api/v1/assets/{asset_id}/status-history`
- `GET /api/v1/assets/{asset_id}/location-history`
- `GET /api/v1/assets/{asset_id}/timeline`
- `GET /api/v1/assets/{asset_id}/tracking`
- `GET /api/v1/assets/{asset_id}/maintenance-history`

Endpoint action yang sudah punya sample:

- `PATCH /api/v1/assets/{asset_id}`
- `POST /api/v1/assets/{asset_id}/attribute-values`
- `POST /api/v1/assets/{asset_id}/ownerships`
- `POST /api/v1/assets/{asset_id}/assignments`
- `POST /api/v1/assignments/{assignment_id}/return`
- `POST /api/v1/assets/{asset_id}/components`
- `POST /api/v1/assets/{asset_id}/status-changes`
- `POST /api/v1/assets/{asset_id}/location-changes`

Seed entity:

- `asset_id`
- `asset_attribute_definition_id`
- `asset_assignment_id`
- `asset_lifecycle_review_id`
- `asset_retirement_request_id`
- `installed_component_asset_id`
- `replacement_component_asset_id`
- `component_install_history_id`
- `component_replace_history_id`

## Asset Components

Tujuan data:

- menampilkan komponen yang saat ini terpasang pada asset;
- menampilkan histori install, remove, dan replace komponen.

Endpoint utama:

- `GET /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/component-history`

Action sample:

- `POST /api/v1/assets/{asset_id}/components`

Seed entity:

- `asset_id`
- `installed_component_asset_id`
- `replacement_component_asset_id`
- `component_install_history_id`
- `component_replace_history_id`

## Asset Lifecycle and Retirement

Tujuan data:

- menampilkan review kondisi dan risiko asset;
- menampilkan rekomendasi replacement;
- mengelola request retirement sampai konfirmasi final.

Endpoint utama:

- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`
- `GET /api/v1/assets/{asset_id}/retirement-requests`

Endpoint detail dan action:

- `GET /api/v1/retirement-requests/{asset_retirement_request_id}`
- `POST /api/v1/assets/{asset_id}/lifecycle-reviews`
- `POST /api/v1/assets/{asset_id}/retirement-requests`
- `POST /api/v1/retirement-requests/{asset_retirement_request_id}/approve`
- `POST /api/v1/retirement-requests/{asset_retirement_request_id}/confirm`

Seed entity:

- `asset_id`
- `asset_lifecycle_review_id`
- `asset_retirement_request_id`

## Asset Transfer List

Tujuan data:

- tabel transfer;
- status monitoring;
- navigasi ke transfer detail.

Endpoint utama:

- `GET /api/v1/asset-transfers`

Endpoint detail:

- `GET /api/v1/asset-transfers/{asset_transfer_id}`

Action sample yang sudah tersedia:

- `POST /api/v1/asset-transfers/{asset_transfer_id}/submit`
- `POST /api/v1/asset-transfers/{asset_transfer_id}/approve`
- `POST /api/v1/asset-transfers/{asset_transfer_id}/complete`

Seed entity:

- `asset_transfer_id`

## Lease Contract List

Tujuan data:

- tabel kontrak sewa/rental/borrowed asset;
- monitoring status kontrak aktif;
- navigasi ke detail kontrak.

Endpoint utama:

- `GET /api/v1/lease-contracts`

Action sample:

- `POST /api/v1/lease-contracts`

Seed entity:

- `lease_contract_id`

## Lease Contract Detail

Tujuan data:

- header kontrak lease;
- daftar asset item dalam kontrak;
- daftar payment lease.

Endpoint utama:

- `GET /api/v1/lease-contracts/{lease_contract_id}`

Endpoint tab:

- `GET /api/v1/lease-contracts/{lease_contract_id}/assets`
- `GET /api/v1/lease-contracts/{lease_contract_id}/payments`

Action sample:

- `POST /api/v1/lease-contracts/{lease_contract_id}/assets`
- `POST /api/v1/lease-contracts/{lease_contract_id}/payments`

## Software License List

Tujuan data:

- tabel lisensi software;
- monitoring expiry dan kapasitas seat;
- navigasi ke detail lisensi.

Endpoint utama:

- `GET /api/v1/software-licenses`

Endpoint pendukung:

- `GET /api/v1/software-products`

Action sample:

- `POST /api/v1/software-products`
- `POST /api/v1/software-licenses`

Seed entity:

- `software_product_id`
- `software_license_id`

## Software License Detail

Tujuan data:

- header lisensi software;
- daftar assignment aktif atau sudah direlease;
- informasi expiry dan capacity.

Endpoint utama:

- `GET /api/v1/software-licenses/{software_license_id}`

Action sample:

- `POST /api/v1/software-licenses/{software_license_id}/assignments`
- `POST /api/v1/software-license-assignments/{software_license_assignment_id}/release`

## Tracking Timeline

Tujuan data:

- histori scan asset;
- visualisasi source scan dan event tracking.

Endpoint utama:

- `GET /api/v1/assets/{asset_id}/tracking`

Action sample:

- `POST /api/v1/tracking/scan-events`
- `POST /api/v1/tracking/scan-events/batch`

Seed entity:

- `asset_id`

## Stocktake List dan Detail

Tujuan data:

- daftar sesi stocktake;
- detail sesi termasuk hasil scan dan status approval.

Endpoint utama:

- `GET /api/v1/stocktakes`
- `GET /api/v1/stocktakes/{stocktake_id}`

Action sample:

- `POST /api/v1/stocktakes/{stocktake_id}/start`
- `POST /api/v1/stocktakes/{stocktake_id}/scan`
- `POST /api/v1/stocktakes/{stocktake_id}/complete`
- `POST /api/v1/stocktakes/{stocktake_id}/approve`

Seed entity:

- `stocktake_id`

## Report Dashboard Asset

Tujuan data:

- discrepancy dashboard;
- missing asset monitoring;
- unverified asset monitoring.

Endpoint:

- `GET /api/v1/reports/location-discrepancies`
- `GET /api/v1/reports/missing-assets`
- `GET /api/v1/reports/unverified-assets`

Query sample:

- `days_since_verified=1`

## Maintenance Master Screens

Tujuan data:

- dropdown dan master admin page untuk maintenance.

Endpoint:

- `GET /api/v1/maintenance/priorities`
- `GET /api/v1/maintenance/contracts`
- `GET /api/v1/maintenance/contracts/{maintenance_contract_id}`
- `GET /api/v1/maintenance/assets/{asset_id}/warranties`
- `GET /api/v1/maintenance/warranties/{asset_warranty_id}`
- `GET /api/v1/maintenance/warranties/{asset_warranty_id}/claims`
- `GET /api/v1/maintenance/entitlements/expiring`
- `GET /api/v1/maintenance/symptom-codes`
- `GET /api/v1/maintenance/failure-modes`
- `GET /api/v1/maintenance/root-cause-codes`
- `GET /api/v1/maintenance/teams`
- `GET /api/v1/maintenance/teams/{maintenance_team_id}`
- `GET /api/v1/maintenance/checklist-templates/{maintenance_checklist_template_id}`

Seed entity:

- `maintenance_priority_id`
- `maintenance_contract_id`
- `maintenance_symptom_code_id`
- `maintenance_failure_mode_id`
- `maintenance_root_cause_code_id`
- `asset_warranty_id`
- `asset_warranty_claim_id`
- `maintenance_team_id`
- `maintenance_checklist_template_id`

## Maintenance Plan List dan Detail

Tujuan data:

- preventive maintenance setup;
- plan asset coverage;
- generated schedule view.

Endpoint utama:

- `GET /api/v1/maintenance/plans`
- `GET /api/v1/maintenance/plans/{maintenance_plan_id}`

Action sample:

- `POST /api/v1/maintenance/plans/{maintenance_plan_id}/assets`
- `POST /api/v1/maintenance/plans/{maintenance_plan_id}/generate`

Catatan frontend:

- form generate schedule sebaiknya mendukung mode kalender biasa,
  trigger meter, trigger condition, dan trigger predictive
- untuk trigger meter, tampilkan input `meter_reading_value`
- untuk trigger condition, tampilkan editor `condition_snapshot`
  sederhana agar planner bisa melihat alasan due generation
- untuk trigger predictive, tampilkan editor `predictive_snapshot`
  dan penjelasan threshold dari `predictive_rule`

Seed entity:

- `maintenance_plan_id`
- `asset_id`

## Maintenance Schedule List dan Detail

Tujuan data:

- daftar schedule;
- detail schedule;
- status planning dan reschedule history.

Endpoint utama:

- `GET /api/v1/maintenance/schedules`
- `GET /api/v1/maintenance/schedules/{maintenance_schedule_id}`

Action sample:

- `POST /api/v1/maintenance/schedules/{maintenance_schedule_id}/confirm`
- `POST /api/v1/maintenance/schedules/{maintenance_schedule_id}/reschedule`
- `GET /api/v1/maintenance/schedules/{maintenance_schedule_id}/events`

Seed entity:

- `maintenance_schedule_id`
- `maintenance_meter_schedule_id`
- `maintenance_condition_schedule_id`
- `maintenance_predictive_schedule_id`

## Maintenance Request List

Tujuan data:

- tabel request;
- status inbox;
- filter berdasarkan priority, vendor, location, atau asset.

Endpoint utama:

- `GET /api/v1/maintenance/requests`

Endpoint pendukung:

- `GET /api/v1/maintenance/priorities`
- `GET /api/v1/maintenance/contracts`
- `GET /api/v1/maintenance/assets/{asset_id}/warranties`
- `GET /api/v1/business-partners`
- `GET /api/v1/asset-locations`

Seed entity:

- `maintenance_request_id`
- `maintenance_contract_id`
- `asset_warranty_id`

## Maintenance Request Detail

Tujuan data:

- header request;
- problem description;
- priority;
- attachment list;
- lifecycle status.

Endpoint utama:

- `GET /api/v1/maintenance/requests/{maintenance_request_id}`
- `GET /api/v1/maintenance/requests/{maintenance_request_id}/attachments`
- `GET /api/v1/maintenance/requests/{maintenance_request_id}/sla-snapshots`

Action sample:

- `POST /api/v1/maintenance/requests/batch`
- `POST /api/v1/maintenance/requests/{maintenance_request_id}/attachments`
- `GET /api/v1/attachments/{attachment_id}`
- `GET /api/v1/attachments/{attachment_id}/download`
- `GET /api/v1/attachments/{attachment_id}/versions`
- `POST /api/v1/attachments/{attachment_id}/versions`
- `GET /api/v1/attachments/{attachment_id}/audit-trail`
- `POST /api/v1/maintenance/requests/{maintenance_request_id}/submit`
- `POST /api/v1/maintenance/requests/{maintenance_request_id}/triage`
- `POST /api/v1/maintenance/requests/{maintenance_request_id}/approve`
- `POST /api/v1/maintenance/requests/{maintenance_request_id}/convert-to-work-order`

Seed entity:

- `maintenance_request_id`
- `maintenance_request_attachment_id`

## Work Order List

Tujuan data:

- daftar WO;
- filter status;
- navigasi ke detail WO.

Endpoint utama:

- `GET /api/v1/maintenance/work-orders`

Seed entity:

- `maintenance_work_order_id`

## Work Order Detail

Tujuan data:

- header WO;
- attachment;
- event log;
- downtime;
- required skill;
- vendor personnel;
- part requirement vs actual usage;
- linked failures;
- lifecycle action state.
- gate checklist/RCA/cost validation sebelum complete dan close.
- gate cancelability dan kunci transaksi operasional setelah status final.

Endpoint utama:

- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}`

Endpoint tab:

- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/attachments`
- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/downtimes`
- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/events`
- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/required-skills`
- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/part-requirements`
- `GET /api/v1/maintenance/work-orders/{maintenance_work_order_id}/vendor-personnel`
- `GET /api/v1/maintenance/failures?work_order_id={maintenance_work_order_id}`

Action sample:

- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/attachments`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/approve`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/assign`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/start`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/required-skills`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/part-requirements`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/vendor-personnel`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/hold`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/resume`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/parts`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/labor-logs`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/downtimes`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/complete`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/verify`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/close`
- `POST /api/v1/maintenance/work-orders/{maintenance_work_order_id}/cancel`

Seed entity:

- `maintenance_work_order_id`

## Failure Detail

Tujuan data:

- menampilkan detail failure, RCA, severity, downtime, dan attachment.

Endpoint utama:

- `GET /api/v1/maintenance/failures`
- `GET /api/v1/maintenance/failures/{maintenance_failure_id}`
- `GET /api/v1/maintenance/failures/{maintenance_failure_id}/attachments`

Action sample:

- `PATCH /api/v1/maintenance/failures/{maintenance_failure_id}`
- `POST /api/v1/maintenance/failures/{maintenance_failure_id}/attachments`

Seed entity:

- `maintenance_failure_id`
- `maintenance_work_order_id`

## Checklist Execution Detail

Tujuan data:

- melihat item checklist;
- hasil inspeksi;
- finding abnormal yang muncul.

Endpoint utama:

- `GET /api/v1/maintenance/checklists/{maintenance_checklist_execution_id}`

Action sample:

- `POST /api/v1/maintenance/checklists/{maintenance_checklist_execution_id}/results`

Seed entity:

- `maintenance_checklist_execution_id`

## Finding Detail

Tujuan data:

- detail finding;
- attachment;
- follow-up request generation.

Endpoint utama:

- `GET /api/v1/maintenance/findings/{maintenance_finding_id}`
- `GET /api/v1/maintenance/findings/{maintenance_finding_id}/attachments`

Action sample:

- `POST /api/v1/maintenance/findings/{maintenance_finding_id}/attachments`
- `POST /api/v1/maintenance/findings/{maintenance_finding_id}/create-request`

Seed entity:

- `maintenance_finding_id`

## Maintenance Dashboard

Tujuan data:

- backlog;
- biaya;
- SLA;
- reliability;
- failure analysis.

Endpoint:

- `GET /api/v1/maintenance/reports/backlog`
- `GET /api/v1/maintenance/reports/cost`
- `GET /api/v1/maintenance/reports/sla`
- `GET /api/v1/maintenance/reports/reliability`
- `GET /api/v1/maintenance/reports/failure-analysis`

Seed entity untuk filter report:

- `asset_id`
- `maintenance_work_order_id`
- `maintenance_failure_id`

## Postman Usage

File `artifacts/postman_seed_environment.json` bisa di-import sebagai Postman
environment.

Field penting di dalamnya:

- `base_url`
- `api_prefix`
- `login_email`
- `access_token`
- `refresh_token`
- seluruh `seed_entities`

Alur pakai:

1. import environment
2. isi `access_token` dari hasil login
3. pakai UUID seed yang tersedia untuk mengetes endpoint detail
