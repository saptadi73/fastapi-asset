# Frontend API Reference

Dokumen ini merangkum endpoint yang sudah diimplementasikan pada tahap awal
Asset Registry MVP. Seluruh endpoint berada di bawah prefix `/api/v1` dan
menggunakan response envelope yang sama agar integrasi frontend konsisten.

## Response Envelope

### Sukses

```json
{
  "success": true,
  "message": "Asset berhasil dibuat.",
  "data": {},
  "error": null,
  "meta": {
    "request_id": "4b06dce1-44a2-48e6-a60d-4124d8dcbeb5",
    "timestamp": "2026-07-27T14:00:00Z",
    "api_version": "v1"
  }
}
```

### Error

```json
{
  "success": false,
  "message": "Asset tidak ditemukan.",
  "data": null,
  "error": {
    "code": "ASSET_NOT_FOUND",
    "message": "Asset tidak ditemukan.",
    "details": {
      "asset_id": "4f69687d-54d2-4d61-a0dd-4e0d9d4cb93f"
    }
  },
  "meta": {
    "request_id": "4b06dce1-44a2-48e6-a60d-4124d8dcbeb5",
    "timestamp": "2026-07-27T14:00:00Z",
    "api_version": "v1"
  }
}
```

## Pagination Contract

Untuk endpoint list:

- `page`: default `1`
- `page_size`: default `20`, maksimum `100`
- `search`: pencarian bebas yang aman
- `sort`: kolom yang diizinkan tiap endpoint
- `order`: `asc` atau `desc`

Frontend dapat membaca `meta.pagination` untuk membangun table, infinite list,
atau pagination control.

## Business Partners

### `POST /business-partners`

Membuat business partner baru beserta role opsional.

Request:

```json
{
  "partner_code": "BP-0001",
  "partner_name": "PT Vendor Mesin",
  "email": "vendor@example.com",
  "phone": "021-555000",
  "is_active": true,
  "roles": [
    {
      "role_type": "SUPPLIER",
      "valid_from": "2026-07-27"
    }
  ]
}
```

### `GET /business-partners`

List partner dengan query:

- `page`
- `page_size`
- `search`
- `sort`: `partner_code`, `partner_name`, `created_at`
- `order`: `asc`, `desc`

### `GET /business-partners/{partner_id}`

Mengambil detail satu partner.

## Asset Categories

### `POST /asset-categories`

Request:

```json
{
  "category_code": "LAPTOP",
  "category_name": "Laptop",
  "description": "Kategori perangkat laptop",
  "is_active": true
}
```

### `GET /asset-categories`

Mengambil seluruh category untuk dropdown, filter, dan form asset.

## Asset Classes

### `POST /asset-classes`

Request:

```json
{
  "class_code": "IT-4Y",
  "class_name": "IT Equipment - 4 Years",
  "sap_asset_class_code": "FA-IT-4Y",
  "default_useful_life_months": 48,
  "is_depreciable": true,
  "is_active": true
}
```

### `GET /asset-classes`

Mengambil seluruh class untuk dropdown finansial/reference.

## Asset Locations

### `POST /asset-locations`

Membuat master lokasi aset.

### `GET /asset-locations`

Mengambil daftar lokasi untuk dropdown perpindahan, filter, dan form asset.

## Asset Attributes

### `POST /asset-attribute-definitions`

Membuat definisi attribute dinamis per `asset_category`.

### `GET /asset-categories/{asset_category_id}/attribute-definitions`

Mengambil daftar definisi attribute untuk membangun form dinamis di frontend.

## Asset Transfers

### `POST /asset-transfers`

Membuat dokumen transfer aset dalam status `DRAFT`.

### `GET /asset-transfers`

Mengambil daftar transfer untuk inbox atau monitoring frontend.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `transfer_number`, `transfer_date`, `status`, `movement_purpose`, `approved_at`, `received_at`
- `order`: `asc`, `desc`
- `status`
- `to_location_id`
- `requested_by`

## Attachments

### `POST /attachments`

Membuat metadata file dan attachment generik untuk `ASSET`,
`ASSET_TRANSFER`, `MAINTENANCE_REQUEST`, atau `MAINTENANCE_WORK_ORDER`.

### `GET /attachments/{attachment_id}`

Mengambil detail attachment beserta metadata file.

### `PATCH /attachments/{attachment_id}`

Mengubah metadata attachment seperti `title`, `description`, `sequence_no`,
`is_primary`, dan `visibility`.

### `DELETE /attachments/{attachment_id}`

Soft delete attachment.

### `GET /attachments/assets/{asset_id}`

Mengambil seluruh attachment untuk asset tertentu.

### `POST /attachments/assets/{asset_id}`

Membuat attachment langsung untuk asset tertentu.

### `GET /maintenance/requests/{request_id}/attachments`

Mengambil seluruh attachment untuk maintenance request tertentu.

### `POST /maintenance/requests/{request_id}/attachments`

Membuat attachment langsung untuk maintenance request tertentu.

Kategori yang direkomendasikan:

- `DAMAGE_PHOTO`
- `OTHER`

### `GET /maintenance/work-orders/{work_order_id}/attachments`

Mengambil seluruh attachment untuk maintenance work order tertentu.

### `POST /maintenance/work-orders/{work_order_id}/attachments`

Membuat attachment langsung untuk maintenance work order tertentu.

Kategori yang direkomendasikan:

- `BEFORE_MAINTENANCE_PHOTO`
- `DURING_MAINTENANCE_PHOTO`
- `AFTER_MAINTENANCE_PHOTO`
- `MAINTENANCE_REPORT`
- `OTHER`

### `GET /attachments/assets/{asset_id}/photos`

Mengambil attachment foto asset saja.

### `POST /attachments/assets/{asset_id}/primary-photo/{attachment_id}`

Menetapkan satu foto utama untuk asset.

### `GET /asset-transfers/{transfer_id}`

Mengambil detail transfer beserta item-item asset di dalamnya.

### `POST /asset-transfers/{transfer_id}/submit`

Mengubah status transfer dari `DRAFT` menjadi `SUBMITTED`.

### `POST /asset-transfers/{transfer_id}/approve`

Mengubah status transfer dari `SUBMITTED` menjadi `APPROVED`.

### `POST /asset-transfers/{transfer_id}/complete`

Menyelesaikan transfer dan menjalankan perubahan operasional secara
transaksional:

- update lokasi aset;
- tutup histori lokasi lama;
- buat histori lokasi baru;
- tutup custodian aktif lama bila custodian baru diberikan;
- buat assignment `PRIMARY_CUSTODIAN` baru bila diperlukan;
- update current state asset.

## Tracking & Stocktake

### `POST /tracking/scan-events`

Mencatat satu event scan QR/barcode/tag untuk verifikasi atau proses stocktake.

Request minimum:

```json
{
  "event_uid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
  "raw_tag_uid": "TAG-0001",
  "scan_type": "VERIFY",
  "scan_source": "MOBILE",
  "scanned_location_id": "44444444-4444-4444-4444-444444444444",
  "scanned_at": "2026-07-27T15:00:00Z",
  "received_at": "2026-07-27T15:00:05Z"
}
```

Catatan:

- `event_uid` dipakai sebagai idempotency key untuk retry/offline sync.
- jika tag dikenali, backend otomatis memperbarui `last_verified_at`;
- jika scan masuk ke sesi stocktake aktif, backend juga membentuk hasil stocktake.

### `POST /tracking/scan-events/batch`

Mengirim banyak scan event sekaligus untuk sinkronisasi perangkat offline.

### `GET /assets/{asset_id}/tracking`

Mengambil gabungan riwayat `scan events` dan `asset verifications` untuk satu aset.

### `POST /stocktakes`

Membuat sesi stocktake baru dalam status `DRAFT`.

Contoh request:

```json
{
  "session_number": "STK-2026-0001",
  "location_id": "44444444-4444-4444-4444-444444444444",
  "scope_type": "LOCATION",
  "planned_start_at": "2026-07-28T01:00:00Z",
  "planned_end_at": "2026-07-28T05:00:00Z",
  "created_by": "55555555-5555-5555-5555-555555555555",
  "notes": "Stocktake bulanan gudang IT"
}
```

### `GET /stocktakes`

List sesi stocktake untuk dashboard operasional.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `session_number`, `planned_start_at`, `status`, `started_at`, `completed_at`
- `order`: `asc`, `desc`
- `status`
- `location_id`

### `GET /stocktakes/{stocktake_session_id}`

Mengambil detail satu sesi stocktake, termasuk:

- informasi lokasi;
- snapshot expected items;
- hasil scan/result yang sudah terbentuk.

### `POST /stocktakes/{stocktake_session_id}/start`

Memulai sesi stocktake dan membuat snapshot expected assets dari lokasi target.

Status:

- `DRAFT` -> `IN_PROGRESS`

### `POST /stocktakes/{stocktake_session_id}/scan`

Mencatat scan dalam konteks sesi stocktake aktif. Endpoint ini memakai payload yang
sama dengan `POST /tracking/scan-events`, tetapi `stocktake_session_id`
diinjeksi dari path.

Hasil scan yang mungkin terbentuk:

- `FOUND`
- `WRONG_LOCATION`
- `UNEXPECTED`
- `DUPLICATE_TAG`
- `UNKNOWN_TAG`

### `POST /stocktakes/{stocktake_session_id}/complete`

Menyelesaikan sesi stocktake.

Status:

- `IN_PROGRESS` -> `COMPLETED`

Saat complete, backend otomatis membuat result `MISSING` untuk asset expected
yang belum pernah dipindai selama sesi.

### `POST /stocktakes/{stocktake_session_id}/approve`

Menyetujui hasil stocktake.

Status:

- `COMPLETED` -> `APPROVED`

## Tracking Reports

### `GET /reports/location-discrepancies`

Mengambil daftar discrepancy lokasi dari hasil verifikasi scan.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `verified_at`, `resolution_status`
- `order`: `asc`, `desc`
- `resolution_status`
- `location_id`

Use case frontend:

- dashboard mismatch lokasi;
- inbox tindak lanjut unauthorized movement;
- filter discrepancy yang masih `OPEN`.

### `GET /reports/missing-assets`

Mengambil daftar hasil `MISSING` dari sesi stocktake.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `created_at`, `resolution_status`, `result_type`
- `order`: `asc`, `desc`
- `stocktake_session_id`
- `resolution_status`
- `location_id`

### `GET /reports/unverified-assets`

Mengambil aset yang belum pernah diverifikasi atau sudah melewati ambang hari
tertentu.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `last_verified_at`, `asset_code`, `asset_name`
- `order`: `asc`, `desc`
- `days_since_verified`: default `30`
- `location_id`

## Maintenance

### `POST /maintenance/priorities`

Membuat master priority maintenance.

Contoh request:

```json
{
  "code": "HIGH",
  "name": "High Priority",
  "severity_level": 3,
  "default_response_minutes": 120,
  "default_resolution_minutes": 480,
  "color_code": "#F59E0B",
  "is_emergency": false,
  "is_active": true
}
```

### `GET /maintenance/priorities`

Mengambil daftar priority untuk dropdown triage dan work order.

### `POST /maintenance/plans`

Membuat preventive maintenance plan.

Aturan backend yang sudah aktif:

- minimal salah satu dari `asset_id` atau `asset_category_id` wajib diisi
- untuk `trigger_type = CALENDAR`, `calendar_interval_value` dan
  `calendar_interval_unit` wajib diisi
- `effective_to` tidak boleh lebih kecil dari `effective_from`

Contoh request:

```json
{
  "plan_code": "PM-CHILLER-001",
  "plan_name": "PM Bulanan Chiller",
  "asset_id": "11111111-1111-1111-1111-111111111111",
  "maintenance_type": "PREVENTIVE",
  "trigger_type": "CALENDAR",
  "calendar_interval_value": 30,
  "calendar_interval_unit": "DAY",
  "default_priority_id": "22222222-2222-2222-2222-222222222222",
  "default_team_id": "33333333-3333-3333-3333-333333333333",
  "estimated_duration_minutes": 180,
  "effective_from": "2026-07-27",
  "next_due_date": "2026-08-26",
  "auto_create_work_order": true
}
```

### `GET /maintenance/plans`

List maintenance plan.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `plan_code`, `plan_name`, `maintenance_type`
- `order`: `asc`, `desc`

### `GET /maintenance/plans/{plan_id}`

Mengambil detail maintenance plan beserta target asset turunannya.

### `POST /maintenance/plans/{plan_id}/assets`

Menambahkan asset target tambahan ke plan.

Aturan backend yang sudah aktif:

- `effective_to` tidak boleh lebih kecil dari `effective_from`
- kombinasi `maintenance_plan_id`, `asset_id`, dan `effective_from` harus unik

### `POST /maintenance/plans/{plan_id}/generate`

Menghasilkan maintenance schedule dari plan aktif.

Perilaku backend:

- target asset digabung dari `plan.asset_id` dan daftar `plan_assets` aktif
- jika `auto_create_work_order = true` pada plan, backend dapat langsung
  membuat work order turunan
- benturan jadwal asset/tim/vendor akan ditolak
- `next_due_date` plan akan dimajukan sesuai interval kalender bila tersedia

### `POST /maintenance/teams`

Membuat master maintenance team.

Contoh request:

```json
{
  "company_id": "11111111-1111-1111-1111-111111111111",
  "team_code": "MEC-01",
  "team_name": "Mechanical Team 01",
  "team_type": "MECHANICAL",
  "default_location_id": "22222222-2222-2222-2222-222222222222",
  "is_active": true
}
```

### `GET /maintenance/teams`

List maintenance team.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `team_code`, `team_name`, `team_type`
- `order`: `asc`, `desc`

### `GET /maintenance/teams/{team_id}`

Mengambil detail team beserta member historisnya.

### `POST /maintenance/teams/{team_id}/members`

Menambahkan member ke team.

Field penting:

- `employee_id`
- `member_role`
- `effective_from`
- `effective_to`
- `is_primary`

### `POST /maintenance/requests`

Membuat maintenance request dalam status awal `DRAFT`.

Field penting untuk frontend:

- `request_number`
- `asset_id`
- `request_type`
- `source_type`
- `priority_id`
- `reported_at`
- `title`
- `problem_description`

### `GET /maintenance/requests`

List maintenance request.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `request_number`, `reported_at`, `status`, `title`
- `order`: `asc`, `desc`

### `GET /maintenance/requests/{request_id}`

Mengambil detail maintenance request beserta asset, priority, lokasi, dan link
work order yang terkait.

### `POST /maintenance/requests/{request_id}/submit`

Status:

- `DRAFT` -> `SUBMITTED`

### `POST /maintenance/requests/{request_id}/triage`

Status:

- `SUBMITTED` -> `TRIAGE`
- `WAITING_INFORMATION` -> `TRIAGE`

Endpoint ini dipakai supervisor/planner untuk memperbarui hasil triage seperti:

- `priority_id`
- `asset_location_id`
- `operating_condition`
- `requested_vendor_partner_id`
- `required_response_at`
- `required_resolution_at`

### `POST /maintenance/requests/{request_id}/approve`

Status:

- `TRIAGE` -> `APPROVED`

### `POST /maintenance/requests/{request_id}/reject`

Status:

- `SUBMITTED` -> `REJECTED`
- `TRIAGE` -> `REJECTED`

`rejection_reason` wajib diisi.

### `POST /maintenance/requests/{request_id}/convert-to-work-order`

Mengonversi request yang sudah `APPROVED` menjadi maintenance work order dan
otomatis membuat junction request-work-order.

Status:

- request `APPROVED` -> `CONVERTED_TO_WORK_ORDER`
- work order baru dibuat dalam status `WAITING_APPROVAL`

### `POST /maintenance/work-orders`

Membuat work order manual dalam status awal `WAITING_APPROVAL`.

### `GET /maintenance/work-orders`

List work order.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `work_order_number`, `created_at`, `status`, `planned_start_at`, `actual_start_at`
- `order`: `asc`, `desc`

### `GET /maintenance/work-orders/{work_order_id}`

Mengambil detail work order beserta asset, priority, request link, dan assignment.

### `POST /maintenance/work-orders/{work_order_id}/approve`

Status:

- `DRAFT` -> `APPROVED`
- `WAITING_APPROVAL` -> `APPROVED`

### `POST /maintenance/work-orders/{work_order_id}/assign`

Status:

- `APPROVED` -> `ASSIGNED`
- `PLANNED` -> `ASSIGNED`

Endpoint ini juga membuat assignment teknisi pada work order.

### `POST /maintenance/work-orders/{work_order_id}/start`

Status:

- `APPROVED` -> `IN_PROGRESS`
- `ASSIGNED` -> `IN_PROGRESS`

Saat work order dimulai, backend juga mencatat histori status aset dan
mengubah status aset menjadi `UNDER_MAINTENANCE`.

### `POST /maintenance/work-orders/{work_order_id}/complete`

Status:

- `IN_PROGRESS` -> `COMPLETED`

### `POST /maintenance/work-orders/{work_order_id}/verify`

Status:

- `COMPLETED` -> `VERIFICATION`

### `POST /maintenance/work-orders/{work_order_id}/close`

Status:

- `VERIFICATION` -> `CLOSED` untuk work order yang `requires_verification = true`
- `COMPLETED` -> `CLOSED` untuk work order yang tidak memerlukan verifikasi

Saat close, backend menutup request terkait ke status `CLOSED` dan
mengembalikan status aset ke `IN_SERVICE`.

### `POST /maintenance/schedules`

Membuat jadwal maintenance aktual.

Contoh request:

```json
{
  "schedule_number": "SCH-2026-0001",
  "maintenance_request_id": "33333333-3333-3333-3333-333333333333",
  "asset_id": "44444444-4444-4444-4444-444444444444",
  "schedule_source": "REQUEST",
  "scheduled_start_at": "2026-07-28T01:00:00Z",
  "scheduled_end_at": "2026-07-28T03:00:00Z",
  "maintenance_team_id": "55555555-5555-5555-5555-555555555555",
  "created_by": "66666666-6666-6666-6666-666666666666",
  "created_at": "2026-07-27T16:00:00Z"
}
```

Aturan backend yang sudah aktif:

- `scheduled_end_at` harus lebih besar dari `scheduled_start_at`
- benturan jadwal asset/tim/vendor pada rentang aktif yang sama akan ditolak

### `GET /maintenance/schedules`

List maintenance schedule.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `schedule_number`, `scheduled_start_at`, `scheduled_end_at`, `status`
- `order`: `asc`, `desc`

### `GET /maintenance/schedules/{schedule_id}`

Mengambil detail schedule beserta asset, request, work order, dan team terkait.

### `POST /maintenance/schedules/{schedule_id}/confirm`

Status:

- `PLANNED` -> `CONFIRMED`

### `POST /maintenance/schedules/{schedule_id}/reschedule`

Mengubah waktu jadwal dan menaikkan `reschedule_count`.

Status yang ditolak:

- `COMPLETED`
- `CANCELLED`

## Assets

### `POST /assets`

Membuat asset registry baru.

Request:

```json
{
  "asset_code": "AST-IT-0001",
  "asset_name": "Laptop Direktur Operasional",
  "asset_category_id": "11111111-1111-1111-1111-111111111111",
  "asset_class_id": "22222222-2222-2222-2222-222222222222",
  "asset_type": "FIXED_ASSET",
  "asset_status": "IN_SERVICE",
  "condition_status": "GOOD",
  "serial_number": "SN-ABC-001",
  "manufacturer_id": "33333333-3333-3333-3333-333333333333",
  "brand": "Lenovo",
  "model": "ThinkPad X1",
  "manufacture_year": 2026,
  "barcode": "899900001",
  "qr_code": "QR-AST-IT-0001",
  "tag_number": "TAG-0001",
  "tracking_status": "TRACKED",
  "in_service_date": "2026-07-27"
}
```

### `GET /assets`

List asset untuk halaman table frontend.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `asset_code`, `asset_name`, `asset_status`, `created_at`
- `order`: `asc`, `desc`

Response item sudah memuat:

- detail category;
- detail class bila ada;
- parent asset ringkas bila ada;
- `version_no` untuk concurrency-aware UI.

### `GET /assets/{asset_id}`

Mengambil detail satu asset untuk halaman detail/edit.

### `PATCH /assets/{asset_id}`

Mengubah asset yang sudah ada. Endpoint ini dipakai untuk update data master
umum, bukan untuk workflow command seperti transfer, assignment, atau status
approval yang nantinya akan memakai endpoint command terpisah.

Contoh request:

```json
{
  "asset_name": "Laptop Direktur Operasional - Updated",
  "condition_status": "FAIR",
  "current_location_id": "44444444-4444-4444-4444-444444444444",
  "updated_by": "55555555-5555-5555-5555-555555555555"
}
```

### `POST /assets/{asset_id}/location-changes`

Mencatat perpindahan lokasi operasional aset dan mengubah `current_location_id`
secara transaksional.

### `GET /assets/{asset_id}/location-history`

Mengambil histori lokasi aset untuk tab history atau audit UI.

### `POST /assets/{asset_id}/assignments`

Mencatat assignment aset, termasuk `PRIMARY_CUSTODIAN`, `USER`, atau
`TECHNICAL_PIC`. Jika assignment baru adalah `PRIMARY_CUSTODIAN`, assignment
aktif sebelumnya akan ditutup otomatis.

### `GET /assets/{asset_id}/assignment-history`

Mengambil histori assignment aset.

### `POST /assets/{asset_id}/attribute-values`

Menyimpan atau memperbarui nilai attribute untuk satu definisi. Endpoint ini
bersifat upsert berdasarkan pasangan `asset_id` dan `attribute_definition_id`.

### `GET /assets/{asset_id}/attribute-values`

Mengambil seluruh nilai attribute asset beserta definition-nya.

### `POST /assets/{asset_id}/ownerships`

Mencatat kepemilikan aset berdasarkan periode berlaku.

### `GET /assets/{asset_id}/ownerships`

Mengambil histori ownership aset.

### `POST /assets/{asset_id}/status-changes`

Mencatat perubahan status dan kondisi aset sambil memperbarui current state
di tabel `assets`.

### `GET /assets/{asset_id}/status-history`

Mengambil histori perubahan status/kondisi aset.

### `GET /assets/{asset_id}/timeline`

Mengambil timeline gabungan dari:

- perubahan lokasi;
- assignment;
- perubahan status.

### `GET /assets/{asset_id}/maintenance-history`

Mengambil histori maintenance asset berbasis work order yang pernah terkait
dengan asset tersebut.

## Error Code Awal

- `REQUEST_VALIDATION_ERROR`
- `BUSINESS_PARTNER_NOT_FOUND`
- `BUSINESS_PARTNER_CONFLICT`
- `ASSET_CATEGORY_NOT_FOUND`
- `ASSET_CATEGORY_CONFLICT`
- `ASSET_CLASS_NOT_FOUND`
- `ASSET_CLASS_CONFLICT`
- `ASSET_NOT_FOUND`
- `ASSET_LOCATION_NOT_FOUND`
- `ASSET_LOCATION_CONFLICT`
- `ASSET_CONFLICT`
- `ASSET_UPDATE_CONFLICT`
- `ASSET_ASSIGNMENT_TARGET_REQUIRED`
- `ASSET_ATTRIBUTE_DEFINITION_NOT_FOUND`
- `ASSET_ATTRIBUTE_DEFINITION_CONFLICT`
- `ASSET_ATTRIBUTE_CATEGORY_MISMATCH`
- `ASSET_ATTRIBUTE_VALUE_INVALID`
- `ASSET_ATTRIBUTE_DATA_TYPE_MISMATCH`
- `ASSET_OWNERSHIP_PARTNER_REQUIRED`
- `ASSET_OWNERSHIP_COMPANY_REQUIRED`
- `ASSET_OWNERSHIP_PERIOD_INVALID`
- `ASSET_OWNERSHIP_OVER_100`
- `ASSET_TRANSFER_NOT_FOUND`
- `ASSET_TRANSFER_ITEMS_REQUIRED`
- `ASSET_TRANSFER_CONFLICT`
- `ASSET_TRANSFER_INVALID_STATUS`
- `ASSET_TRANSFER_SOURCE_LOCATION_MISMATCH`
- `ATTACHMENT_NOT_FOUND`
- `FILE_RECORD_NOT_FOUND`
- `ATTACHMENT_CONFLICT`
- `ATTACHMENT_ENTITY_NOT_FOUND`
- `ATTACHMENT_ENTITY_TYPE_UNSUPPORTED`
- `ASSET_SCAN_EVENT_CONFLICT`
- `ASSET_SCAN_EVENT_NOT_FOUND`
- `STOCKTAKE_SESSION_NOT_FOUND`
- `STOCKTAKE_SESSION_CONFLICT`
- `STOCKTAKE_SESSION_INVALID_STATUS`
- `MAINTENANCE_PRIORITY_NOT_FOUND`
- `MAINTENANCE_PRIORITY_CONFLICT`
- `MAINTENANCE_REQUEST_NOT_FOUND`
- `MAINTENANCE_REQUEST_CONFLICT`
- `MAINTENANCE_REQUEST_INVALID_STATUS`
- `MAINTENANCE_PLAN_NOT_FOUND`
- `MAINTENANCE_PLAN_CONFLICT`
- `MAINTENANCE_PLAN_SCOPE_REQUIRED`
- `MAINTENANCE_PLAN_TRIGGER_INVALID`
- `MAINTENANCE_PLAN_PERIOD_INVALID`
- `MAINTENANCE_PLAN_ASSET_CONFLICT`
- `MAINTENANCE_PLAN_ASSET_PERIOD_INVALID`
- `MAINTENANCE_PLAN_TARGETS_EMPTY`
- `MAINTENANCE_PLAN_GENERATION_CONFLICT`
- `MAINTENANCE_WORK_ORDER_NOT_FOUND`
- `MAINTENANCE_WORK_ORDER_CONFLICT`
- `MAINTENANCE_WORK_ORDER_INVALID_STATUS`
- `MAINTENANCE_WORK_ORDER_ASSIGNMENT_CONFLICT`
- `MAINTENANCE_WORK_ORDER_TIME_INVALID`
- `MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE`
- `MAINTENANCE_TEAM_NOT_FOUND`
- `MAINTENANCE_TEAM_CONFLICT`
- `MAINTENANCE_TEAM_MEMBER_CONFLICT`
- `MAINTENANCE_TEAM_MEMBER_PERIOD_INVALID`
- `MAINTENANCE_SCHEDULE_NOT_FOUND`
- `MAINTENANCE_SCHEDULE_CONFLICT`
- `MAINTENANCE_SCHEDULE_INVALID_STATUS`
- `MAINTENANCE_SCHEDULE_WINDOW_INVALID`
- `MAINTENANCE_SCHEDULE_OVERLAP`
- `ASSET_PARENT_INVALID`

## Catatan Integrasi Frontend

- Gunakan `error.code` sebagai kontrak stabil untuk handling UI.
- Seluruh tanggal dikirim sebagai ISO 8601.
- UUID menjadi identifier utama semua entitas.
- `204 No Content` tidak dipakai; semua endpoint JSON selalu mengembalikan envelope.
- Swagger/OpenAPI tetap menjadi sumber kontrak live, sedangkan dokumen ini
  ditujukan sebagai ringkasan praktis untuk tim frontend.
