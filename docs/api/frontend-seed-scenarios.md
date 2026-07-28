# Frontend Seed Scenarios

Dokumen ini menjelaskan bagaimana data seed live dibentuk pada **Tuesday, July 28, 2026**
agar tim frontend bisa memahami:

- endpoint mana yang menghasilkan data untuk endpoint berikutnya;
- entity mana yang cocok dipakai untuk halaman detail;
- urutan call API yang paling masuk akal untuk layar utama.

Referensi artefak live:

- `artifacts/seed_smoke_results.json`
- `artifacts/frontend_endpoint_samples.json`

## Seed Entities

Entity utama hasil seed yang paling berguna untuk frontend:

- `asset_id`
- `asset_lifecycle_review_id`
- `asset_retirement_request_id`
- `installed_component_asset_id`
- `replacement_component_asset_id`
- `component_install_history_id`
- `component_replace_history_id`
- `asset_transfer_id`
- `stocktake_id`
- `maintenance_plan_id`
- `maintenance_schedule_id`
- `maintenance_request_id`
- `maintenance_work_order_id`
- `maintenance_failure_id`
- `maintenance_checklist_execution_id`
- `maintenance_finding_id`

Seluruh nilai aktual UUID tersedia di `seed_entities` dalam file
`artifacts/frontend_endpoint_samples.json`.

## Scenario Matrix

### 1. Authentication

Tujuan:

- mendapatkan bearer token;
- memuat profil user aktif untuk header, avatar, role guard, dan audit info.

Endpoint:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Output penting:

- `tokens.access_token`
- `tokens.refresh_token`
- `user.id`
- `user.roles`
- `user.permissions`

### 2. Business Partner Master

Tujuan:

- menyediakan partner supplier/vendor yang nanti dipakai oleh asset ownership,
  maintenance request, schedule vendor, dan work order vendor.

Endpoint:

- `POST /api/v1/business-partners`
- `GET /api/v1/business-partners`
- `GET /api/v1/business-partners/{partner_id}`

Output penting:

- `business_partner_id`

### 3. Asset Registry Master

Tujuan:

- membentuk master category, class, dan location sebelum asset dibuat.

Endpoint:

- `POST /api/v1/asset-categories`
- `GET /api/v1/asset-categories`
- `POST /api/v1/asset-classes`
- `GET /api/v1/asset-classes`
- `POST /api/v1/asset-locations`
- `GET /api/v1/asset-locations`
- `POST /api/v1/asset-attribute-definitions`
- `GET /api/v1/asset-categories/{asset_category_id}/attribute-definitions`

Output penting:

- `asset_category_id`
- `asset_class_id`
- `origin_location_id`
- `destination_location_id`
- `asset_attribute_definition_id`

### 4. Asset Registry Transactional

Tujuan:

- membentuk satu asset lengkap berikut histori dan relasi turunannya.

Endpoint:

- `POST /api/v1/assets`
- `GET /api/v1/assets`
- `GET /api/v1/assets/{asset_id}`
- `PATCH /api/v1/assets/{asset_id}`
- `POST /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/component-history`
- `POST /api/v1/assets/{asset_id}/lifecycle-reviews`
- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`
- `POST /api/v1/assets/{asset_id}/attribute-values`
- `GET /api/v1/assets/{asset_id}/attribute-values`
- `POST /api/v1/assets/{asset_id}/ownerships`
- `GET /api/v1/assets/{asset_id}/ownerships`
- `POST /api/v1/assets/{asset_id}/assignments`
- `GET /api/v1/assets/{asset_id}/assignment-history`
- `POST /api/v1/assets/{asset_id}/status-changes`
- `GET /api/v1/assets/{asset_id}/status-history`
- `POST /api/v1/assets/{asset_id}/location-changes`
- `GET /api/v1/assets/{asset_id}/location-history`
- `GET /api/v1/assets/{asset_id}/timeline`

Output penting:

- `asset_id`
- `asset_tag_number`
- asset sudah memiliki replacement planning fields
- asset sudah memiliki komponen aktif hasil flow replace
- asset sudah memiliki satu lifecycle review dengan recommendation `REPLACE`

### 5. Asset Retirement Flow

Tujuan:

- menampilkan retirement request yang dibuat dan dikonfirmasi pada Monday, July 27, 2026;
- memberi sample approval flow retirement yang sudah terhubung ke status asset.

Endpoint:

- `POST /api/v1/assets/{asset_id}/retirement-requests`
- `GET /api/v1/assets/{asset_id}/retirement-requests`
- `GET /api/v1/retirement-requests/{asset_retirement_request_id}`
- `POST /api/v1/retirement-requests/{asset_retirement_request_id}/approve`
- `POST /api/v1/retirement-requests/{asset_retirement_request_id}/confirm`

Output penting:

- `asset_retirement_request_id`
- retirement request berstatus akhir `CONFIRMED`
- asset sample berstatus akhir `DISPOSED`
- timeline asset memuat event lifecycle review dan retirement

### 6. Asset Component Flow

Tujuan:

- menampilkan install dan replace komponen pada asset utama;
- memberi sample current components dan component history untuk frontend.

Endpoint:

- `POST /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/components`
- `GET /api/v1/assets/{asset_id}/component-history`

Output penting:

- `installed_component_asset_id`
- `replacement_component_asset_id`
- asset utama berakhir dengan komponen pengganti terpasang
- histori memuat action `INSTALL` lalu `REPLACE`

### 7. Lease Contract Flow

Tujuan:

- menampilkan contoh kontrak lease aktif pada Monday, July 27, 2026;
- memberi sample item aset yang dilease dan payment bulan berjalan.

Endpoint:

- `POST /api/v1/lease-contracts`
- `GET /api/v1/lease-contracts`
- `GET /api/v1/lease-contracts/{lease_contract_id}`
- `POST /api/v1/lease-contracts/{lease_contract_id}/assets`
- `GET /api/v1/lease-contracts/{lease_contract_id}/assets`
- `POST /api/v1/lease-contracts/{lease_contract_id}/payments`
- `GET /api/v1/lease-contracts/{lease_contract_id}/payments`

Output penting:

- `lease_contract_id`
- contract aktif periode `2026-07-01` sampai `2026-12-31`
- asset item lease untuk aset smoke utama
- payment periode `2026-07-01` sampai `2026-07-31`

### 8. Software License Flow

Tujuan:

- menampilkan contoh software license aktif pada Monday, July 27, 2026;
- memberi sample assignment dan release seat lisensi.

Endpoint:

- `POST /api/v1/software-products`
- `GET /api/v1/software-products`
- `POST /api/v1/software-licenses`
- `GET /api/v1/software-licenses`
- `GET /api/v1/software-licenses/{software_license_id}`
- `POST /api/v1/software-licenses/{software_license_id}/assignments`
- `POST /api/v1/software-license-assignments/{software_license_assignment_id}/release`

Output penting:

- `software_product_id`
- `software_license_id`
- license aktif dengan `expiry_date` `2026-08-15`
- seat sempat terpakai lalu kembali tersedia setelah release

### 9. Asset Transfer

Tujuan:

- membentuk skenario perpindahan asset dari draft sampai complete.

Endpoint:

- `POST /api/v1/asset-transfers`
- `GET /api/v1/asset-transfers`
- `GET /api/v1/asset-transfers/{transfer_id}`
- `POST /api/v1/asset-transfers/{transfer_id}/submit`
- `POST /api/v1/asset-transfers/{transfer_id}/approve`
- `POST /api/v1/asset-transfers/{transfer_id}/complete`

Output penting:

- `asset_transfer_id`

### 10. Tracking dan Stocktake

Tujuan:

- membentuk histori scan dan sesi stocktake yang punya lifecycle lengkap.

Endpoint:

- `POST /api/v1/tracking/scan-events`
- `POST /api/v1/tracking/scan-events/batch`
- `GET /api/v1/assets/{asset_id}/tracking`
- `POST /api/v1/stocktakes`
- `GET /api/v1/stocktakes`
- `GET /api/v1/stocktakes/{stocktake_id}`
- `POST /api/v1/stocktakes/{stocktake_id}/start`
- `POST /api/v1/stocktakes/{stocktake_id}/scan`
- `POST /api/v1/stocktakes/{stocktake_id}/complete`
- `POST /api/v1/stocktakes/{stocktake_id}/approve`

Output penting:

- `stocktake_id`

### 11. Asset Reports

Tujuan:

- memberi dataset awal untuk dashboard discrepancy dan verification.

Endpoint:

- `GET /api/v1/reports/location-discrepancies`
- `GET /api/v1/reports/missing-assets`
- `GET /api/v1/reports/unverified-assets`

### 12. Maintenance Master Data

Tujuan:

- membentuk seluruh master yang diperlukan sebelum request, schedule, atau work order.

Endpoint:

- `POST /api/v1/maintenance/priorities`
- `GET /api/v1/maintenance/priorities`
- `POST /api/v1/maintenance/symptom-codes`
- `GET /api/v1/maintenance/symptom-codes`
- `POST /api/v1/maintenance/failure-modes`
- `GET /api/v1/maintenance/failure-modes`
- `POST /api/v1/maintenance/root-cause-codes`
- `GET /api/v1/maintenance/root-cause-codes`
- `POST /api/v1/maintenance/checklist-templates`
- `GET /api/v1/maintenance/checklist-templates/{template_id}`
- `POST /api/v1/maintenance/teams`
- `GET /api/v1/maintenance/teams`
- `GET /api/v1/maintenance/teams/{team_id}`
- `POST /api/v1/maintenance/teams/{team_id}/members`

Output penting:

- `maintenance_priority_id`
- `maintenance_symptom_code_id`
- `maintenance_failure_mode_id`
- `maintenance_root_cause_code_id`
- `maintenance_checklist_template_id`
- `maintenance_team_id`

### 13. Preventive Maintenance Planning

Tujuan:

- membentuk plan asset, generate schedule, lalu mengubah status schedule.

Endpoint:

- `POST /api/v1/maintenance/plans`
- `GET /api/v1/maintenance/plans`
- `GET /api/v1/maintenance/plans/{plan_id}`
- `POST /api/v1/maintenance/plans/{plan_id}/assets`
- `POST /api/v1/maintenance/plans/{plan_id}/generate`
- `GET /api/v1/maintenance/schedules`
- `GET /api/v1/maintenance/schedules/{schedule_id}`
- `POST /api/v1/maintenance/schedules/{schedule_id}/confirm`
- `POST /api/v1/maintenance/schedules/{schedule_id}/reschedule`
- `GET /api/v1/maintenance/schedules/{schedule_id}/events`

Output penting:

- `maintenance_plan_id`
- `maintenance_schedule_id`

Tambahan seed yang sekarang tersedia:

- calendar plan dengan confirm + reschedule + event history
- meter plan dengan `meter_reading_value` yang memicu `METER_TRIGGER`
- condition plan dengan `condition_snapshot` yang memicu `CONDITION_TRIGGER`
- predictive plan dengan `predictive_snapshot` yang memicu
  `PREDICTIVE_TRIGGER`
- seed entity tambahan:
  `maintenance_meter_plan_id`, `maintenance_meter_schedule_id`,
  `maintenance_condition_plan_id`, `maintenance_condition_schedule_id`,
  `maintenance_predictive_plan_id`, `maintenance_predictive_schedule_id`

### 10. Maintenance Request

Tujuan:

- membentuk request corrective/breakdown dengan attachment dan approval flow.

Endpoint:

- `POST /api/v1/maintenance/requests/batch`
- `POST /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/requests/{request_id}`
- `POST /api/v1/maintenance/requests/{request_id}/attachments`
- `GET /api/v1/maintenance/requests/{request_id}/attachments`
- `POST /api/v1/maintenance/requests/{request_id}/submit`
- `POST /api/v1/maintenance/requests/{request_id}/triage`
- `POST /api/v1/maintenance/requests/{request_id}/approve`

Output penting:

- `maintenance_request_id`
- `maintenance_batch_request_parent_id`
- sample triage menghasilkan SLA snapshot yang memuat vendor entitlement source
  dan recommended execution mode untuk referensi UI frontend

Tambahan seed yang sekarang tersedia:

- asset warranty claim
- entitlement expiry report
- batch request multi-asset dengan parent-child traceability

### 11. Work Order Lifecycle

Tujuan:

- mengubah request approved menjadi work order yang berjalan sampai selesai.

Endpoint:

- `POST /api/v1/maintenance/requests/{request_id}/convert-to-work-order`
- `GET /api/v1/maintenance/work-orders`
- `GET /api/v1/maintenance/work-orders/{work_order_id}`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/attachments`
- `GET /api/v1/maintenance/work-orders/{work_order_id}/attachments`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/approve`
- `POST /api/v1/maintenance/skills`
- `GET /api/v1/maintenance/skills`
- `POST /api/v1/maintenance/employees/{employee_id}/skills`
- `GET /api/v1/maintenance/employees/{employee_id}/skills`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/required-skills`
- `GET /api/v1/maintenance/work-orders/{work_order_id}/required-skills`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/assign`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/start`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/part-requirements`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/vendor-personnel`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/parts`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/labor-logs`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/downtimes`
- `GET /api/v1/maintenance/work-orders/{work_order_id}/downtimes`
- `GET /api/v1/maintenance/work-orders/{work_order_id}/events`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/complete`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/verify`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/close`
- `GET /api/v1/maintenance/work-orders/{work_order_id}`

Output penting:

- `maintenance_work_order_id`

### 12. Failures, Findings, Checklist, dan Follow-up

Tujuan:

- membentuk data failure, RCA, checklist execution, finding, lalu follow-up request.

Endpoint:

- `POST /api/v1/maintenance/work-orders/{work_order_id}/failures`
- `GET /api/v1/maintenance/failures`
- `GET /api/v1/maintenance/failures/{failure_id}`
- `PATCH /api/v1/maintenance/failures/{failure_id}`
- `POST /api/v1/maintenance/failures/{failure_id}/attachments`
- `GET /api/v1/maintenance/failures/{failure_id}/attachments`
- `POST /api/v1/maintenance/work-orders/{work_order_id}/checklists`
- `GET /api/v1/maintenance/checklists/{checklist_id}`
- `POST /api/v1/maintenance/checklists/{checklist_id}/results`
- `GET /api/v1/maintenance/checklists/{checklist_id}`
- `GET /api/v1/maintenance/findings/{finding_id}`
- `POST /api/v1/maintenance/findings/{finding_id}/attachments`
- `GET /api/v1/maintenance/findings/{finding_id}/attachments`
- `POST /api/v1/maintenance/findings/{finding_id}/create-request`

Output penting:

- `maintenance_failure_id`
- `maintenance_checklist_execution_id`
- `maintenance_finding_id`

### 13. Maintenance Reports dan History

Tujuan:

- memastikan dashboard dan tab history frontend punya data nyata.

Endpoint:

- `GET /api/v1/maintenance/reports/backlog`
- `GET /api/v1/maintenance/reports/cost`
- `GET /api/v1/maintenance/reports/sla`
- `GET /api/v1/maintenance/reports/reliability`
- `GET /api/v1/maintenance/reports/failure-analysis`
- `GET /api/v1/assets/{asset_id}/maintenance-history`

## Recommended Frontend Flows

### Asset List Page

Urutan call:

1. `GET /api/v1/asset-categories`
2. `GET /api/v1/asset-classes`
3. `GET /api/v1/asset-locations`
4. `GET /api/v1/assets?page=1&page_size=20`

Catatan:

- filter dropdown sebaiknya dimuat lebih dulu;
- detail row asset sudah cukup kaya untuk table utama;
- saat user membuka detail, lanjutkan ke flow Asset Detail.

### Asset Detail Page

Urutan call:

1. `GET /api/v1/assets/{asset_id}`
2. `GET /api/v1/assets/{asset_id}/attribute-values`
3. `GET /api/v1/assets/{asset_id}/ownerships`
4. `GET /api/v1/assets/{asset_id}/assignment-history`
5. `GET /api/v1/assets/{asset_id}/components`
6. `GET /api/v1/assets/{asset_id}/component-history`
7. `GET /api/v1/assets/{asset_id}/status-history`
8. `GET /api/v1/assets/{asset_id}/location-history`
9. `GET /api/v1/assets/{asset_id}/lifecycle-reviews`
10. `GET /api/v1/assets/{asset_id}/retirement-requests`
11. `GET /api/v1/assets/{asset_id}/timeline`
12. `GET /api/v1/assets/{asset_id}/tracking`
13. `GET /api/v1/assets/{asset_id}/maintenance-history`

Gunakan ID:

- `asset_id` dari `seed_entities`

Lifecycle yang sudah tersedia di seed:

- assignment dibuat lalu dikembalikan
- status berubah ke `IDLE`
- transfer dibuat lalu selesai
- location change tambahan dicatat
- komponen awal di-install lalu diganti komponen pengganti
- lifecycle review dibuat dengan recommendation `REPLACE`
- retirement request dibuat, diapprove, lalu dikonfirmasi

### Asset Transfer Monitoring Page

Urutan call:

1. `GET /api/v1/asset-transfers`
2. `GET /api/v1/asset-transfers/{asset_transfer_id}`

Bila frontend perlu menampilkan status chip lifecycle:

- seed sudah menghasilkan state `DRAFT -> SUBMITTED -> APPROVED -> COMPLETED`

### Stocktake Detail Page

Urutan call:

1. `GET /api/v1/stocktakes`
2. `GET /api/v1/stocktakes/{stocktake_id}`

Catatan:

- seed sudah melewati state `DRAFT/PLANNED -> IN_PROGRESS -> COMPLETED -> APPROVED`

### Maintenance Request List Page

Urutan call:

1. `GET /api/v1/maintenance/priorities`
2. `GET /api/v1/maintenance/requests?page=1&page_size=20`

Opsional filter master:

- `GET /api/v1/business-partners`
- `GET /api/v1/asset-locations`

### Maintenance Request Detail Page

Urutan call:

1. `GET /api/v1/maintenance/requests/{request_id}`
2. `GET /api/v1/maintenance/requests/{request_id}/attachments`

Lifecycle yang sudah tersedia di seed:

- create
- submit
- triage
- approve
- convert ke work order

### Maintenance Schedule List and Detail

Urutan call:

1. `GET /api/v1/maintenance/schedules`
2. `GET /api/v1/maintenance/schedules/{schedule_id}`

Lifecycle yang sudah tersedia di seed:

- generated from plan
- confirmed
- rescheduled

### Maintenance Work Order Detail Page

Urutan call:

1. `GET /api/v1/maintenance/work-orders/{work_order_id}`
2. `GET /api/v1/maintenance/work-orders/{work_order_id}/attachments`
3. `GET /api/v1/maintenance/work-orders/{work_order_id}/required-skills`
4. `GET /api/v1/maintenance/work-orders/{work_order_id}/part-requirements`
5. `GET /api/v1/maintenance/work-orders/{work_order_id}/vendor-personnel`
6. `GET /api/v1/maintenance/work-orders/{work_order_id}/downtimes`
7. `GET /api/v1/maintenance/work-orders/{work_order_id}/events`
8. `GET /api/v1/maintenance/failures?work_order_id={work_order_id}`

Lifecycle yang sudah tersedia di seed:

- waiting approval
- approved
- required skill defined
- assigned
- employee skill validated during assignment
- in progress
- vendor personnel checked in and checked out
- planned part created and synchronized after part usage
- actual part dan labor cost tervalidasi terhadap rollup transaksi saat complete
- completed
- verification
- closed

### Failure Detail Page

Urutan call:

1. `GET /api/v1/maintenance/failures?work_order_id={work_order_id}`
2. `GET /api/v1/maintenance/failures/{failure_id}`
3. `GET /api/v1/maintenance/failures/{failure_id}/attachments`

Seed sudah menyediakan:

- failure awal;
- update RCA;
- attachment failure.

### Checklist and Finding Page

Urutan call:

1. `GET /api/v1/maintenance/checklists/{checklist_id}`
2. `GET /api/v1/maintenance/findings/{finding_id}`
3. `GET /api/v1/maintenance/findings/{finding_id}/attachments`

Seed sudah menyediakan:

- checklist execution;
- checklist result dengan kondisi abnormal;
- finding hasil checklist;
- follow-up request dari finding.

### Maintenance Dashboard

Urutan call:

1. `GET /api/v1/maintenance/reports/backlog`
2. `GET /api/v1/maintenance/reports/cost`
3. `GET /api/v1/maintenance/reports/sla`
4. `GET /api/v1/maintenance/reports/reliability`
5. `GET /api/v1/maintenance/reports/failure-analysis`

## Practical Guidance

- Untuk sample request dan response nyata, buka `frontend_endpoint_samples.json`.
- Untuk mengetahui UUID entity yang valid saat uji manual, buka `seed_entities`.
- Untuk memahami mengapa sebuah entity punya state tertentu, baca urutan skenario
  pada dokumen ini.
- Untuk kontrak field lengkap, tetap gunakan OpenAPI live dan
  `docs/api/frontend-api-reference.md`.
