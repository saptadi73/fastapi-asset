# Frontend API Reference

Dokumen ini merangkum endpoint yang sudah diimplementasikan pada tahap awal
Asset Registry MVP. Seluruh endpoint berada di bawah prefix `/api/v1` dan
menggunakan response envelope yang sama agar integrasi frontend konsisten.

## Live Seed Reference

Untuk kebutuhan frontend, backend sekarang juga menghasilkan artefak sample
response dari live seed run pada **Tuesday, July 28, 2026**.

File yang bisa dijadikan rujukan:

- `artifacts/seed_smoke_results.json`
- `artifacts/frontend_endpoint_samples.json`
- `artifacts/postman_seed_environment.json`
- `artifacts/postman_seed_collection.json`
- `docs/api/frontend-seed-scenarios.md`
- `docs/api/frontend-page-endpoint-map.md`
- `docs/api/frontend-functional-blueprint.md`
- `docs/implementation-gap-checklist.md`
- `docs/implementation-roadmap.md`

Isi penting:

- `seed_entities`: kumpulan ID hasil seed seperti `asset_id`, `request_id`,
  `work_order_id`, `schedule_id`, `finding_id`
- `endpoint_samples`: contoh `request_json`, `query_params`, dan
  `response_json` nyata untuk endpoint yang sudah diuji

Rekomendasi pemakaian untuk frontend:

- mulai dari dokumen ini untuk memahami kontrak endpoint
- buka `frontend_endpoint_samples.json` untuk melihat response riil
- gunakan `postman_seed_environment.json` bila frontend ingin uji cepat di Postman
- gunakan `postman_seed_collection.json` untuk import request siap pakai
- buka `frontend-seed-scenarios.md` untuk memahami alur pembentukan datanya
- buka `frontend-page-endpoint-map.md` untuk mapping halaman ke endpoint
- buka `frontend-functional-blueprint.md` untuk menu, halaman, dashboard, dan workflow
- buka `implementation-gap-checklist.md` untuk backlog gap implementasi baseline
- buka `implementation-roadmap.md` untuk urutan sprint implementasi backend
- gunakan `seed_entities` saat perlu mengetes endpoint detail secara manual

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

## Auth Requirement

Mulai batch auth saat ini, endpoint bisnis pada modul `assets`,
`attachments`, `business-partners`, `maintenance`, `tracking`, `stocktakes`,
dan `reports` sudah memakai bearer token.

Gunakan header:

```text
Authorization: Bearer <access_token>
```

Bila token tidak ada atau tidak valid, backend mengembalikan `401`.
Bila token valid tetapi permission tidak cukup, backend mengembalikan `403`.

Catatan penting untuk frontend:

- field audit seperti `created_by`, `updated_by`, `actor_id`, `scanned_by`,
  `uploaded_by`, dan `deleted_by` pada endpoint bisnis utama tidak perlu lagi
  dikirim manual bila aksinya dilakukan oleh user yang sedang login;
- backend akan mengisi field tersebut dari bearer token aktif.

## Authentication

### `POST /auth/login`

Login dengan email dan password.

Request:

```json
{
  "email": "admin@example.com",
  "password": "Admin12345!"
}
```

Response `data` berisi:

- `user`
- `tokens.access_token`
- `tokens.refresh_token`
- `tokens.token_type`
- `tokens.access_token_expires_at`
- `tokens.refresh_token_expires_at`

### `POST /auth/refresh`

Memutar refresh token dan menghasilkan pasangan token baru.

Request:

```json
{
  "refresh_token": "<jwt-refresh-token>"
}
```

Catatan frontend:

- simpan refresh token terbaru setelah refresh berhasil
- refresh token lama tidak boleh dipakai ulang

### `POST /auth/logout`

Logout session aktif berdasarkan bearer access token.

Header:

- `Authorization: Bearer <access_token>`

### `GET /auth/me`

Mengambil profil user yang sedang login.

Header:

- `Authorization: Bearer <access_token>`

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

Catatan:

- `requested_by` akan diisi otomatis dari user login.

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
`ASSET_TRANSFER`, `MAINTENANCE_REQUEST`, `MAINTENANCE_WORK_ORDER`, atau
`MAINTENANCE_FINDING`.

Catatan:

- `created_by` dan `file.uploaded_by` diisi otomatis dari user login;
- `captured_by` akan diisi user login bila tidak dikirim eksplisit.

### `GET /attachments/{attachment_id}`

Mengambil detail attachment beserta metadata file.

### `GET /attachments/{attachment_id}/download`

Mengambil referensi download attachment dari file aktif saat ini.

Respons `data` berisi:

- `attachment`: metadata attachment lengkap
- `current_version`: metadata versi file aktif
- `download_url`: URL API aman berumur pendek untuk mengakses detail file aktif
- `download_mode`: `SIGNED_API_URL`
- `expires_at`: waktu kedaluwarsa link download aman

### `GET /attachments/downloads/{download_token}`

Meresolusikan token download aman menjadi referensi file yang bisa dipakai
frontend untuk membuka atau meneruskan proses download.

Respons `data` berisi:

- metadata attachment
- metadata file utama
- metadata versi file yang dituju
- `storage_provider`
- `storage_bucket`
- `storage_object_key`
- `mime_type`
- `file_name`
- `expires_at`

### `GET /attachments/{attachment_id}/versions`

Mengambil seluruh versi file attachment, diurutkan dari versi terbaru ke
terlama.

Use case frontend:

- tab version history dokumen
- timeline revisi evidentiary file
- penanda versi aktif vs versi lama

### `POST /attachments/{attachment_id}/versions`

Mengunggah versi file baru untuk attachment yang sama.

Efek backend:

- versi aktif sebelumnya akan ditandai `is_current = false`
- metadata file utama akan diarahkan ke versi terbaru
- `current_version_no` akan dinaikkan otomatis

### `GET /attachments/{attachment_id}/audit-trail`

Mengambil jejak lifecycle attachment, termasuk:

- pembuatan attachment
- upload versi awal
- upload versi revisi
- penerbitan secure download link
- penggunaan secure download token
- update metadata attachment
- soft delete bila sudah terjadi

Catatan backend:

- audit trail kini disimpan sebagai event append-only pada tabel file event
- frontend dapat memperlakukannya sebagai timeline immutable

### `PATCH /attachments/{attachment_id}`

Mengubah metadata attachment seperti `title`, `description`, `sequence_no`,
`is_primary`, dan `visibility`.

### `DELETE /attachments/{attachment_id}`

Soft delete attachment.

### `GET /attachments/assets/{asset_id}`

Mengambil seluruh attachment untuk asset tertentu.

### `POST /attachments/assets/{asset_id}`

Membuat attachment langsung untuk asset tertentu.

Catatan:

- `created_by` dan `file.uploaded_by` diisi otomatis dari user login.

### `GET /maintenance/requests/{request_id}/attachments`

Mengambil seluruh attachment untuk maintenance request tertentu.

### `POST /maintenance/requests/{request_id}/attachments`

Membuat attachment langsung untuk maintenance request tertentu.

Kategori yang direkomendasikan:

- `DAMAGE_PHOTO`
- `OTHER`

Untuk setiap item attachment pada frontend, sebaiknya sediakan action:

- lihat metadata
- lihat referensi download
- lihat version history
- upload versi revisi
- lihat audit trail

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

### `GET /maintenance/findings/{finding_id}/attachments`

Mengambil seluruh attachment untuk maintenance finding tertentu.

### `POST /maintenance/findings/{finding_id}/attachments`

Membuat attachment langsung untuk maintenance finding tertentu.

Kategori yang direkomendasikan:

- `FINDING_PHOTO`
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
  "notes": "Stocktake bulanan gudang IT"
}
```

Catatan:

- `created_by` diisi otomatis dari user login.

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

Catatan:

- `actor_id` diisi otomatis dari user login.

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

Catatan:

- `scanned_by` diisi otomatis dari user login.

### `POST /stocktakes/{stocktake_session_id}/complete`

Menyelesaikan sesi stocktake.

Status:

- `IN_PROGRESS` -> `COMPLETED`

Saat complete, backend otomatis membuat result `MISSING` untuk asset expected
yang belum pernah dipindai selama sesi.

Catatan:

- `actor_id` diisi otomatis dari user login.

### `POST /stocktakes/{stocktake_session_id}/approve`

Menyetujui hasil stocktake.

Status:

- `COMPLETED` -> `APPROVED`

Catatan:

- `actor_id` diisi otomatis dari user login.

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

### `POST /maintenance/contracts`

Membuat master maintenance contract vendor.

### `GET /maintenance/contracts`

Mengambil daftar maintenance contract beserta coverage asset yang sudah
terhubung.

### `GET /maintenance/contracts/{contract_id}`

Mengambil detail satu maintenance contract.

### `POST /maintenance/contracts/{contract_id}/assets`

Menambahkan coverage asset ke maintenance contract.

Aturan backend yang sudah aktif:

- periode coverage harus berada di dalam periode contract
- kombinasi `contract`, `asset`, dan `coverage_start_date` harus unik

### `POST /maintenance/warranties`

Membuat master warranty untuk asset.

### `POST /maintenance/warranties/{warranty_id}/claims`

Membuat claim warranty untuk satu warranty tertentu.

Validasi backend:

- `claim_date` harus berada di dalam periode coverage warranty
- `claim_date` tidak boleh melewati `claim_deadline_date` bila deadline tersedia
- `replacement_asset_id` tidak boleh sama dengan asset yang diklaim
- `cost_covered` dan `cost_not_covered` tidak boleh negatif

### `GET /maintenance/assets/{asset_id}/warranties`

Mengambil seluruh warranty milik asset tertentu.

### `GET /maintenance/warranties/{warranty_id}`

Mengambil detail satu warranty.

### `GET /maintenance/warranties/{warranty_id}/claims`

Mengambil histori claim warranty untuk satu warranty.

### `GET /maintenance/entitlements/expiring`

Mengambil report entitlement yang akan segera berakhir.

Query:

- `days_ahead`: default `30`, minimum `1`, maksimum `365`

Use case frontend:

- dashboard expiry warranty
- dashboard expiry maintenance contract coverage
- reminder renewal atau extension contract
- panel operasional untuk melihat coverage yang hampir habis

### `POST /maintenance/symptom-codes`

Membuat master symptom code untuk klasifikasi gejala awal kerusakan.

### `GET /maintenance/symptom-codes`

Mengambil daftar symptom code untuk dropdown form failure analysis.

### `POST /maintenance/failure-modes`

Membuat master failure mode.

### `GET /maintenance/failure-modes`

Mengambil daftar failure mode untuk dropdown analisis failure.

### `POST /maintenance/root-cause-codes`

Membuat master root cause code.

### `GET /maintenance/root-cause-codes`

Mengambil daftar root cause code untuk dropdown root cause analysis.

### `POST /maintenance/checklist-templates`

Membuat checklist template maintenance beserta item-item pemeriksaannya.

Aturan backend yang sudah aktif:

- template wajib memiliki minimal satu item
- `effective_to` tidak boleh lebih kecil dari `effective_from`
- `sequence_no` item harus unik dalam satu template

### `GET /maintenance/checklist-templates/{template_id}`

Mengambil detail checklist template beserta seluruh itemnya.

### `POST /maintenance/plans`

Membuat preventive maintenance plan.

Aturan backend yang sudah aktif:

- minimal salah satu dari `asset_id` atau `asset_category_id` wajib diisi
- untuk `trigger_type = CALENDAR`, `CALENDAR_OR_METER`, atau
  `CALENDAR_AND_METER`, `calendar_interval_value` dan
  `calendar_interval_unit` wajib diisi
- untuk `trigger_type = METER`, `CALENDAR_OR_METER`, atau
  `CALENDAR_AND_METER`, `meter_interval` wajib diisi
- untuk `trigger_type = CONDITION`, `condition_rule` wajib diisi
- untuk `trigger_type = PREDICTIVE`, `predictive_rule` wajib diisi
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
- payload sekarang dapat membawa `meter_reading_value`,
  `condition_snapshot`, `predictive_snapshot`, `trigger_evaluated_at`, dan
  `generation_reason`
- backend mengevaluasi due sesuai `trigger_type`:
  `CALENDAR`, `METER`, `CALENDAR_OR_METER`, `CALENDAR_AND_METER`,
  `CONDITION`, `PREDICTIVE`, atau `MANUAL`
- `next_due_date` plan akan dimajukan sesuai interval kalender bila tersedia
- `next_due_meter_value` akan dimajukan sesuai `meter_interval` untuk
  trigger berbasis meter
- `schedule_source` akan diisi lebih spesifik:
  `PREVENTIVE_PLAN`, `METER_TRIGGER`, `CONDITION_TRIGGER`, atau
  `PREDICTIVE_TRIGGER`

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

Catatan entitlement:

- request tetap dapat dibuat tanpa contract atau warranty
- penentuan coverage aktif diproses pada tahap triage

### `POST /maintenance/requests/batch`

Membuat beberapa maintenance request sekaligus untuk banyak asset.

Perilaku backend:

- tiap `asset_id` dalam batch harus unik
- tiap `request_number` dalam batch harus unik
- request pertama menjadi parent, request berikutnya memakai
  `parent_request_id` ke request pertama
- bila item batch mengirim `maintenance_contract_id` atau `warranty_id`,
  backend memvalidasi entitlement terhadap asset item tersebut

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
- `maintenance_contract_id`
- `warranty_id`
- `requested_vendor_partner_id`
- `required_response_at`
- `required_resolution_at`

Kemampuan backend yang sekarang aktif:

- validasi contract aktif terhadap asset dan tanggal triage
- validasi warranty aktif terhadap asset dan tanggal triage
- validasi `claim_deadline_date` warranty agar entitlement claim tidak dipakai
  setelah lewat masa klaim
- auto-resolve contract aktif bila payload tidak mengirim contract tetapi asset
  punya coverage yang cocok
- auto-resolve warranty aktif bila payload tidak mengirim warranty tetapi asset
  punya warranty aktif
- validasi vendor agar tetap sesuai vendor entitlement contract atau warranty
- bila contract dan warranty menunjuk vendor berbeda, frontend wajib mengirim
  `requested_vendor_partner_id` eksplisit
- default vendor dari warranty lebih dulu, lalu contract, bila frontend tidak
  mengirim vendor
- default SLA target dari contract atau priority bila frontend tidak mengirim
  target manual

### `GET /maintenance/requests/{request_id}/sla-snapshots`

Mengambil histori snapshot SLA untuk satu maintenance request.

Use case frontend:

- panel SLA pada request detail
- audit target historis walaupun master priority atau contract berubah
- indikator escalation dasar berdasarkan `snapshot_payload.escalation_due_at`
  dan `snapshot_payload.escalation_triggered`
- badge vendor entitlement dan rekomendasi mode eksekusi dari
  `snapshot_payload.resolved_vendor_source` dan
  `snapshot_payload.recommended_execution_mode`
- panel contract support scope dari `snapshot_payload.contract_support_scope`
- panel warranty claim context dari
  `snapshot_payload.warranty_claim_deadline_date`

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

Validasi tambahan:

- contract dan warranty yang sudah dipilih pada request akan dicek ulang saat
  konversi
- `maintenance_contract_id` dan `warranty_id` diwariskan ke work order
- `vendor_partner_id` akan default ke vendor hasil triage bila frontend tidak
  mengirim vendor eksplisit
- bila frontend mengirim `vendor_partner_id`, backend akan memvalidasi bahwa
  vendor tersebut masih cocok dengan entitlement contract atau warranty aktif

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

Mengambil detail work order beserta asset, priority, request link, assignment,
downtime, event lifecycle, part requirement, vendor personnel, part usage, dan
labor log.

### `POST /maintenance/work-orders/{work_order_id}/approve`

Status:

- `DRAFT` -> `APPROVED`
- `WAITING_APPROVAL` -> `APPROVED`

### `POST /maintenance/work-orders/{work_order_id}/assign`

Status:

- `APPROVED` -> `ASSIGNED`
- `PLANNED` -> `ASSIGNED`

Endpoint ini juga membuat assignment teknisi pada work order.

Perilaku backend:

- bila work order memiliki `required_skills`, employee yang di-assign harus punya
  skill aktif pada tanggal assignment
- bila work order punya `maintenance_team_id`, employee harus menjadi anggota
  aktif tim pada tanggal assignment

### `POST /maintenance/work-orders/{work_order_id}/start`

Status:

- `APPROVED` -> `IN_PROGRESS`
- `ASSIGNED` -> `IN_PROGRESS`

Saat work order dimulai, backend juga mencatat histori status aset dan
mengubah status aset menjadi `UNDER_MAINTENANCE`.

Rule tambahan:

- work order harus memiliki assignment lebih dulu
- work order `VENDOR` wajib sudah memiliki `vendor_personnel`
- seluruh assignment yang ada akan divalidasi ulang terhadap skill aktif

### `POST /maintenance/skills`

Membuat master maintenance skill.

### `GET /maintenance/skills`

Mengambil daftar master maintenance skill untuk form planner, work order skill
matrix, dan master data UI.

### `POST /maintenance/employees/{employee_id}/skills`

Menambahkan skill maintenance ke employee.

Perilaku backend:

- `valid_to` tidak boleh lebih kecil dari `valid_from`
- bila skill mewajibkan sertifikasi, `certificate_number` wajib diisi

### `GET /maintenance/employees/{employee_id}/skills`

Mengambil daftar skill maintenance employee beserta master skill yang terkait.

### `POST /maintenance/work-orders/{work_order_id}/hold`

Status:

- `IN_PROGRESS` -> `ON_HOLD`

Dipakai saat eksekusi berhenti sementara, misalnya menunggu part, vendor, atau
approval lanjutan.

### `POST /maintenance/work-orders/{work_order_id}/resume`

Status:

- `ON_HOLD` -> `IN_PROGRESS`

### `POST /maintenance/work-orders/{work_order_id}/cancel`

Status yang saat ini diizinkan:

- `DRAFT`
- `WAITING_APPROVAL`
- `APPROVED`
- `PLANNED`
- `ASSIGNED`
- `ON_HOLD`

Validasi tambahan yang sudah aktif:

- work order yang sudah pernah `start` tidak dapat dibatalkan
- work order yang sudah memiliki `part usage`, `labor log`, `failure record`,
  atau `checklist execution` tidak dapat dibatalkan

### `POST /maintenance/work-orders/{work_order_id}/complete`

Status:

- `IN_PROGRESS` -> `COMPLETED`
- `ON_HOLD` -> `COMPLETED`

Validasi tambahan yang sudah aktif:

- untuk work order `PREVENTIVE`, `INSPECTION`, `CALIBRATION`, atau work order
  yang berasal dari `maintenance_plan`, minimal harus ada satu checklist dengan
  status `COMPLETED`
- untuk work order `BREAKDOWN`, minimal harus ada satu failure, seluruh failure
  harus `RESOLVED` atau `CLOSED`, dan RCA wajib terisi
- `actual_part_cost` harus sama dengan rollup transaksi part work order
- `actual_labor_cost` harus sama dengan rollup labor log work order
- `actual_vendor_cost` tetap dikirim dari payload karena belum punya rollup
  transaksi vendor terpisah

### `POST /maintenance/work-orders/{work_order_id}/verify`

Status:

- `COMPLETED` -> `VERIFICATION`

### `POST /maintenance/work-orders/{work_order_id}/close`

Status:

- `VERIFICATION` -> `CLOSED` untuk work order yang `requires_verification = true`
- `COMPLETED` -> `CLOSED` untuk work order yang tidak memerlukan verifikasi

Saat close, backend menutup request terkait ke status `CLOSED` dan
mengembalikan status aset ke `IN_SERVICE`.

Validasi tambahan yang sudah aktif:

- bila tipe work order mewajibkan checklist, checklist completed harus sudah ada
- checklist work order yang sudah dibuat harus berada pada status `COMPLETED`
- untuk work order `BREAKDOWN`, seluruh failure harus sudah memiliki RCA dan
  status akhir `RESOLVED` atau `CLOSED`
- finding yang `requires_follow_up = true` harus sudah memiliki follow-up
  request atau sudah selesai
- biaya aktual part dan labor akan dihitung ulang dari log operasional

### `POST /maintenance/work-orders/{work_order_id}/checklists`

Memulai checklist execution untuk work order.

Aturan backend yang sudah aktif:

- work order harus berada pada status yang masih mengizinkan checklist
- `checklist_template_id` bisa dikirim eksplisit atau diambil dari maintenance
  plan yang terkait

Catatan state machine:

- checklist boleh dimulai saat work order masih `APPROVED`, `ASSIGNED`,
  `IN_PROGRESS`, atau `COMPLETED`
- tetapi transaksi operasional baru seperti failure, part usage, dan labor log
  hanya boleh ditambah saat work order masih aktif dieksekusi

### `POST /maintenance/work-orders/{work_order_id}/required-skills`

Menetapkan skill wajib pada work order.

Perilaku backend:

- tidak bisa ditambah bila work order sudah `CLOSED` atau `CANCELLED`
- jika master skill punya `certification_required=true`, requirement work order
  ikut dianggap membutuhkan sertifikasi
- endpoint ini menambah audit event `REQUIRED_SKILL_ADDED`

### `GET /maintenance/work-orders/{work_order_id}/required-skills`

Mengambil daftar skill wajib pada work order untuk planner dan assignment screen.

### `POST /maintenance/work-orders/{work_order_id}/part-requirements`

Mencatat kebutuhan part terencana sebelum actual usage dicatat.

### `POST /maintenance/work-orders/{work_order_id}/parts`

Part usage saat ini hanya boleh dicatat saat work order berada di status aktif:

- `APPROVED`
- `ASSIGNED`
- `IN_PROGRESS`
- `ON_HOLD`

Part usage tidak lagi diizinkan setelah work order masuk `COMPLETED` atau
`VERIFICATION`.

### `POST /maintenance/work-orders/{work_order_id}/labor-logs`

Labor log saat ini hanya boleh dicatat saat work order berada di status aktif:

- `APPROVED`
- `ASSIGNED`
- `IN_PROGRESS`
- `ON_HOLD`

Labor log tidak lagi diizinkan setelah work order masuk `COMPLETED` atau
`VERIFICATION`.

Perilaku backend:

- menolak penambahan bila work order sudah `CLOSED` atau `CANCELLED`
- `reserved_quantity` tidak boleh lebih besar dari `required_quantity`
- endpoint ini menambah audit event `PART_REQUIREMENT_ADDED`

### `GET /maintenance/work-orders/{work_order_id}/part-requirements`

Mengambil daftar kebutuhan part terencana untuk work order.

Kegunaan frontend:

- tampilkan tab material planning
- bedakan planned quantity, reserved quantity, issued quantity, dan returned
  quantity
- gunakan `requirement_status` untuk badge readiness

### `POST /maintenance/work-orders/{work_order_id}/vendor-personnel`

Mencatat teknisi atau personel vendor yang hadir pada work order.

Perilaku backend:

- menolak penambahan bila work order sudah `CLOSED` atau `CANCELLED`
- `check_out_at` tidak boleh lebih kecil dari `check_in_at`
- endpoint ini menambah audit event `VENDOR_PERSONNEL_ADDED`

### `GET /maintenance/work-orders/{work_order_id}/vendor-personnel`

Mengambil daftar teknisi vendor yang terlibat pada work order.

Kegunaan frontend:

- tampilkan tab eksternal/vendor execution
- tampilkan histori check-in dan check-out vendor di lapangan
- gunakan untuk halaman approval biaya vendor dan bukti kehadiran

### `POST /maintenance/work-orders/{work_order_id}/parts`

Mencatat penggunaan spare part pada work order.

Perilaku backend:

- `asset_id` part usage mengikuti asset pada work order
- biaya aktual part pada work order dihitung ulang dari seluruh part usage yang
  tersimpan
- jika ada `part requirement` untuk `part_item_id` yang sama, backend
  menyinkronkan `issued_quantity`, `returned_quantity`, dan `requirement_status`

### `POST /maintenance/work-orders/{work_order_id}/labor-logs`

Mencatat jam kerja teknisi pada work order.

Perilaku backend:

- jika `duration_minutes` tidak dikirim tetapi `ended_at` ada, backend akan
  menghitung durasi otomatis
- jika `labor_cost` tidak dikirim tetapi `hourly_rate` dan durasi tersedia,
  backend akan menghitung biaya otomatis
- biaya aktual labor pada work order dihitung ulang dari labor log yang
  tersimpan

### `POST /maintenance/work-orders/{work_order_id}/downtimes`

Mencatat downtime yang terkait ke work order.

Perilaku backend:

- `asset_id` downtime otomatis mengikuti asset pada work order
- `maintenance_request_id` akan ikut terhubung bila work order berasal dari
  maintenance request
- jika `ended_at` dikirim tetapi `duration_minutes` kosong, backend menghitung
  durasi downtime otomatis
- setiap pencatatan downtime otomatis membuat event `DOWNTIME_RECORDED`

Contoh request:

```json
{
  "downtime_type": "UNPLANNED",
  "started_at": "2026-07-27T08:00:00Z",
  "ended_at": "2026-07-27T09:30:00Z",
  "production_loss_quantity": 120.5,
  "unit_of_measure": "PCS",
  "reason": "Motor conveyor trip mendadak"
}
```

### `POST /maintenance/work-orders/{work_order_id}/failures`

Mencatat kejadian failure teknis pada work order.

Perilaku backend:

- `asset_id` dan `maintenance_request_id` diambil dari konteks work order;
- `created_by` diisi otomatis dari user login;
- `detected_by_employee_id` default ke user login bila tidak dikirim;
- event `FAILURE_RECORDED` otomatis ditambahkan ke histori work order;
- `downtime_minutes` dihitung otomatis bila `failure_started_at` dan
  `failure_ended_at` tersedia.

Field penting untuk frontend:

- `failure_number`
- `detected_at`
- `failure_mode_id`
- `symptom_code_id`
- `failure_description`
- `failure_severity`
- `root_cause_code_id`
- `root_cause_description`
- `corrective_action`
- `preventive_action`
- `repeat_failure`
- `caused_shutdown`
- `safety_incident`

### `GET /maintenance/work-orders/{work_order_id}/downtimes`

Mengambil daftar downtime pada work order untuk tab downtime, analytics durasi,
atau ringkasan loss produksi.

Field penting pada response item:

- `downtime_type`
- `started_at`
- `ended_at`
- `duration_minutes`
- `production_loss_quantity`
- `unit_of_measure`
- `reason`

### `GET /maintenance/work-orders/{work_order_id}/events`

Mengambil histori event lifecycle work order secara kronologis.

Use case frontend:

- timeline progress work order
- audit aktivitas work order
- badge atau log otomatis untuk checklist, finding, part issue, labor log, dan
  downtime

Contoh event yang saat ini dapat muncul:

- `CREATED`
- `APPROVED`
- `ASSIGNED`
- `STARTED`
- `DOWNTIME_RECORDED`
- `CHECKLIST_COMPLETED`
- `FINDING_CREATED`
- `PART_ISSUED`
- `LABOR_LOGGED`
- `COMPLETED`
- `VERIFIED`
- `CLOSED`

### `GET /maintenance/failures`

List asset failure untuk inbox analisis reliability atau investigasi teknis.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `failure_number`, `detected_at`, `failure_severity`, `status`, `created_at`
- `order`: `asc`, `desc`
- `asset_id`
- `work_order_id`
- `status`
- `failure_mode_id`
- `root_cause_code_id`
- `date_from`: ISO datetime
- `date_to`: ISO datetime

### `GET /maintenance/failures/{failure_id}`

Mengambil detail satu failure, termasuk symptom code, failure mode, root cause,
dan tindakan korektif/preventif.

### `PATCH /maintenance/failures/{failure_id}`

Memperbarui failure, melengkapi RCA, atau menutup failure setelah analisis.

Field yang umum dipakai frontend:

- `failure_mode_id`
- `symptom_code_id`
- `failure_description`
- `failure_severity`
- `asset_condition_before`
- `asset_condition_after`
- `caused_shutdown`
- `safety_incident`
- `repeat_failure`
- `temporary_action`
- `root_cause_code_id`
- `root_cause_description`
- `corrective_action`
- `preventive_action`
- `failure_started_at`
- `failure_ended_at`
- `downtime_minutes`
- `status`: `OPEN`, `UNDER_ANALYSIS`, `RESOLVED`, `CLOSED`

Perilaku backend:

- bila `failure_started_at` dan `failure_ended_at` tersedia, `downtime_minutes`
  akan dihitung otomatis jika tidak dikirim;
- jika payload sudah berisi root cause atau action RCA, backend akan membuat
  event work order `RCA_FINALIZED`;
- perubahan umum tanpa finalisasi RCA akan tercatat sebagai event
  `FAILURE_UPDATED`.

### `GET /maintenance/checklists/{checklist_id}`

Mengambil detail checklist execution, hasil tiap item, dan finding yang
terbentuk.

### `POST /maintenance/checklists/{checklist_id}/results`

Menyimpan seluruh hasil checklist lalu menutup checklist execution.

Perilaku backend:

- seluruh item wajib yang ada di template harus diisi
- hasil abnormal otomatis membuat `maintenance finding`
- `overall_result` checklist akan menjadi `PASS` atau `FAIL`

### `GET /maintenance/findings/{finding_id}`

Mengambil detail satu finding hasil checklist.

### `POST /maintenance/findings/{finding_id}/create-request`

Membuat follow-up maintenance request dari finding.

Perilaku backend:

- source request yang dibuat adalah `CHECKLIST_FINDING`
- finding yang sama tidak boleh membuat request lebih dari satu kali
- jika `submit = true`, request baru langsung dibuat dalam status `SUBMITTED`

### `GET /maintenance/failures/{failure_id}/attachments`

Mengambil attachment bukti failure dan root cause untuk satu failure.

Kategori yang direkomendasikan:

- `FAILURE_PHOTO`
- `ROOT_CAUSE_EVIDENCE`
- `OTHER`

### `POST /maintenance/failures/{failure_id}/attachments`

Membuat attachment langsung untuk asset failure tertentu.

Catatan:

- `created_by` dan `file.uploaded_by` diisi otomatis dari user login;
- `captured_by` akan diisi user login bila tidak dikirim eksplisit.

### `GET /maintenance/reports/backlog`

Mengambil ringkasan backlog operasional maintenance untuk dashboard.

Field utama pada response:

- `request_backlog_count`
- `overdue_request_count`
- `open_work_order_count`
- `overdue_work_order_count`
- `active_schedule_count`
- `overdue_schedule_count`
- `generated_at`

### `GET /maintenance/reports/cost`

Mengambil daftar biaya aktual maintenance per work order.

Query:

- `page`
- `page_size`
- `search`
- `sort`: `work_order_number`, `maintenance_type`, `status`, `actual_end_at`, `closed_at`, `actual_part_cost`, `actual_labor_cost`, `actual_vendor_cost`
- `order`: `asc`, `desc`
- `asset_id`
- `maintenance_type`
- `date_from`: ISO datetime
- `date_to`: ISO datetime

Field utama pada response item:

- `work_order_number`
- `asset_code`
- `asset_name`
- `maintenance_type`
- `status`
- `actual_part_cost`
- `actual_labor_cost`
- `actual_vendor_cost`
- `total_actual_cost`
- `actual_end_at`
- `closed_at`

### `GET /maintenance/reports/sla`

Mengambil ringkasan kepatuhan SLA maintenance request.

Query:

- `date_from`: ISO datetime
- `date_to`: ISO datetime

Field utama pada response:

- `response_sla_target_count`
- `response_sla_met_count`
- `response_sla_breached_count`
- `response_sla_compliance_pct`
- `resolution_sla_target_count`
- `resolution_sla_met_count`
- `resolution_sla_breached_count`
- `resolution_sla_compliance_pct`

Catatan implementasi saat ini:

- response SLA dihitung dari `required_response_at` vs `triaged_at`
- resolution SLA dihitung dari `required_resolution_at` vs status akhir request
  dan `updated_at`

### `GET /maintenance/reports/reliability`

Mengambil ringkasan reliability maintenance dari work order dan downtime yang
sudah tercatat.

Query:

- `date_from`: ISO datetime
- `date_to`: ISO datetime

Field utama pada response:

- `completed_repair_count`
- `breakdown_work_order_count`
- `preventive_work_order_count`
- `unplanned_work_order_count`
- `planned_work_order_count`
- `mttr_minutes`
- `total_downtime_minutes`
- `average_downtime_minutes`
- `planned_vs_unplanned_ratio`
- `repeat_failure_asset_count`

Catatan implementasi saat ini:

- MTTR dihitung dari rata-rata durasi work order yang sudah punya
  `actual_start_at` dan `actual_end_at`
- downtime diambil dari tabel `maintenance_downtimes`
- ratio planned vs unplanned memakai klasifikasi work order yang sudah ada

### `GET /maintenance/reports/failure-analysis`

Mengambil analytics berbasis failure untuk reliability dashboard dan RCA view.

Query:

- `asset_id`
- `failure_mode_id`
- `root_cause_code_id`
- `date_from`: ISO datetime
- `date_to`: ISO datetime

Field utama pada response:

- `failure_count`
- `open_failure_count`
- `under_analysis_count`
- `resolved_failure_count`
- `closed_failure_count`
- `repeat_failure_count`
- `repeat_failure_rate_pct`
- `rca_completed_count`
- `rca_pending_count`
- `rca_completion_rate_pct`
- `caused_shutdown_count`
- `safety_incident_count`
- `total_downtime_minutes`
- `average_downtime_minutes`
- `mtbf_hours`
- `top_failure_modes`
- `top_root_causes`
- `top_assets`

Catatan implementasi saat ini:

- MTBF saat ini diperkirakan dari interval antar `detected_at` failure per aset
  karena jam operasi aktual aset belum disimpan sebagai sumber KPI.

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

Mengubah waktu jadwal, menaikkan `reschedule_count`, dan menulis audit event
reschedule yang menyimpan waktu lama dan waktu baru.

Status yang ditolak:

- `COMPLETED`
- `CANCELLED`

### `GET /maintenance/schedules/{schedule_id}/events`

Mengambil history event untuk schedule.

Contoh event yang bisa muncul:

- `CREATED`
- `GENERATED`
- `CONFIRMED`
- `RESCHEDULED`

Catatan frontend:

- `event_payload` pada event `RESCHEDULED` memuat `previous_scheduled_start_at`,
  `previous_scheduled_end_at`, `new_scheduled_start_at`,
  `new_scheduled_end_at`, dan `reschedule_count`
- `event_payload` pada event `GENERATED` memuat konteks trigger seperti
  `trigger_type`, `schedule_source`, `meter_reading_value`,
  `condition_snapshot`, dan `predictive_snapshot`

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

Catatan:

- `created_by` dan `updated_by` diisi otomatis dari user login.

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
  "current_location_id": "44444444-4444-4444-4444-444444444444"
}
```

Catatan:

- `updated_by` diisi otomatis dari user login.

### `POST /assets/{asset_id}/location-changes`

Mencatat perpindahan lokasi operasional aset dan mengubah `current_location_id`
secara transaksional.

Catatan:

- `recorded_by` diisi otomatis dari user login.

### `GET /assets/{asset_id}/location-history`

Mengambil histori lokasi aset untuk tab history atau audit UI.

### `POST /assets/{asset_id}/assignments`

Mencatat assignment aset, termasuk `PRIMARY_CUSTODIAN`, `USER`, atau
`TECHNICAL_PIC`. Jika assignment baru adalah `PRIMARY_CUSTODIAN`, assignment
aktif sebelumnya akan ditutup otomatis.

### `POST /assignments/{assignment_id}/return`

Menutup assignment aktif dengan `returned_at` dan mengubah
`assignment_status` menjadi `RETURNED`.

Untuk assignment `PRIMARY_CUSTODIAN`, backend juga mengosongkan
`current_primary_custodian_id` bila assignment yang dikembalikan masih menjadi
custodian aktif asset.

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

## Lease Domain

### `POST /lease-contracts`

Membuat lease contract baru untuk aset sewa, rental, borrowed asset, atau
partner placement.

Perilaku backend:

- `end_date` tidak boleh lebih kecil dari `start_date`
- `extension_option_end_date` tidak boleh lebih kecil dari `end_date`

### `GET /lease-contracts`

Mengambil daftar lease contract untuk halaman list lease.

### `GET /lease-contracts/{contract_id}`

Mengambil detail lease contract beserta asset item dan payment yang terkait.

### `POST /lease-contracts/{contract_id}/assets`

Menambahkan asset lease item ke contract.

Perilaku backend:

- periode item harus berada dalam periode contract
- `lease_end_date` tidak boleh lebih kecil dari `lease_start_date`
- satu aset tidak boleh memiliki active lease item yang overlap

### `GET /lease-contracts/{contract_id}/assets`

Mengambil daftar asset item pada lease contract.

### `POST /lease-contracts/{contract_id}/payments`

Mencatat payment schedule atau realisasi payment lease contract.

Perilaku backend:

- periode payment harus berada dalam periode contract
- `period_end` tidak boleh lebih kecil dari `period_start`
- `due_date` tidak boleh lebih kecil dari `period_start`

### `GET /lease-contracts/{contract_id}/payments`

Mengambil daftar payment lease contract.

## Software License Domain

### `POST /software-products`

Membuat master software product.

### `GET /software-products`

Mengambil daftar software product untuk form pembuatan lisensi dan master data.

### `POST /software-licenses`

Membuat software license baru.

Perilaku backend:

- `expiry_date` tidak boleh lebih kecil dari `start_date`
- `license_key_encrypted` disimpan, tetapi tidak diekspos di response biasa
- `used_quantity` dihitung dari assignment aktif, bukan dari input user

### `GET /software-licenses`

Mengambil daftar software license dengan indikator:

- `available_quantity`
- `capacity_full`
- `expires_soon`

Catatan tanggal:

- indikator `expires_soon` pada sample seed dihitung terhadap Monday, July 27, 2026

### `GET /software-licenses/{license_id}`

Mengambil detail software license beserta assignment aktif dan histori release.

### `POST /software-licenses/{license_id}/assignments`

Mencatat assignment software license ke asset atau named user.

Perilaku backend:

- target harus tepat satu: `asset_id` atau `employee_id`
- assignment ditolak bila kapasitas license penuh
- assignment ditolak bila license belum aktif atau sudah expired pada tanggal
  assignment

### `POST /software-license-assignments/{assignment_id}/release`

Merelease assignment software license yang masih aktif.

Perilaku backend:

- `released_at` tidak boleh lebih kecil dari `assigned_at`
- `used_quantity` license akan dihitung ulang otomatis setelah release

## Asset Lifecycle and Retirement

### `POST /assets/{asset_id}/lifecycle-reviews`

Mencatat hasil lifecycle review untuk asset.

Perilaku backend:

- satu asset hanya boleh punya satu review per `review_date`
- `condition_score` wajib berada pada rentang `0..100`
- `risk_score` bila diisi wajib berada pada rentang `0..100`
- response membawa `replacement_recommendation` untuk badge atau callout frontend

### `GET /assets/{asset_id}/lifecycle-reviews`

Mengambil histori lifecycle review per asset dengan urutan terbaru lebih dulu.

### `POST /assets/{asset_id}/retirement-requests`

Membuat retirement request untuk asset.

Perilaku backend:

- asset retired/disposed tidak bisa dibuatkan request baru
- hanya satu retirement request terbuka diperbolehkan per asset
- `retirement_number` harus unik

### `GET /assets/{asset_id}/retirement-requests`

Mengambil daftar retirement request per asset.

### `GET /retirement-requests/{retirement_id}`

Mengambil detail retirement request untuk panel atau drawer detail.

### `POST /retirement-requests/{retirement_id}/approve`

Mengubah status retirement request dari `REQUESTED` menjadi `APPROVED`.

### `POST /retirement-requests/{retirement_id}/confirm`

Mengonfirmasi retirement request dan sekaligus memperbarui status asset.

Perilaku backend:

- hanya request berstatus `REQUESTED` atau `APPROVED` yang bisa dikonfirmasi
- `final_asset_status` harus `RETIRED` atau `DISPOSED`
- konfirmasi membuat histori status asset otomatis
- `retirement_date` asset diisi dari `effective_date`
- pada sample seed Monday, July 27, 2026, asset berakhir pada status `DISPOSED`

## Asset Components

### `POST /assets/{asset_id}/components`

Mencatat perubahan komponen pada asset host.

Perilaku backend:

- `INSTALL` wajib hanya membawa `installed_component_asset_id`
- `REMOVE` wajib hanya membawa `removed_component_asset_id`
- `REPLACE` wajib membawa kedua field tersebut
- komponen yang dipasang tidak boleh masih terpasang pada asset lain
- backend mencegah self-reference dan siklus hierarchy
- `parent_asset_id` komponen diperbarui secara transaksional

### `GET /assets/{asset_id}/components`

Mengambil daftar komponen yang saat ini terpasang pada asset.

### `GET /assets/{asset_id}/component-history`

Mengambil histori install/remove/replace komponen pada asset.

### `POST /assets/{asset_id}/status-changes`

Mencatat perubahan status dan kondisi aset sambil memperbarui current state
di tabel `assets`.

Catatan:

- `changed_by` diisi otomatis dari user login.

### `GET /assets/{asset_id}/status-history`

Mengambil histori perubahan status/kondisi aset.

### `GET /assets/{asset_id}/timeline`

Mengambil timeline gabungan dari:

- perubahan lokasi;
- assignment;
- perubahan komponen;
- perubahan status;
- lifecycle review;
- retirement request atau konfirmasi retirement.

### `GET /assets/{asset_id}/maintenance-history`

Mengambil histori maintenance asset berbasis work order yang pernah terkait
dengan asset tersebut.

Ringkasan tambahan yang sekarang tersedia per item:

- `downtime_count`
- `total_downtime_minutes`
- `labor_log_count`
- `failure_count`
- `work_order_event_count`

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
- `ASSET_LIFECYCLE_REVIEW_CONFLICT`
- `ASSET_RETIREMENT_NOT_FOUND`
- `ASSET_RETIREMENT_ALREADY_OPEN`
- `ASSET_RETIREMENT_CONFLICT`
- `ASSET_RETIREMENT_INVALID_STATUS`
- `ASSET_RETIREMENT_FINAL_STATUS_INVALID`
- `ASSET_ALREADY_RETIRED`
- `ASSET_COMPONENT_ACTION_INVALID`
- `ASSET_COMPONENT_SELF_REFERENCE`
- `ASSET_COMPONENT_NOT_INSTALLED`
- `ASSET_COMPONENT_ALREADY_ATTACHED`
- `ASSET_COMPONENT_CYCLE`
- `ASSET_COMPONENT_REPLACE_SAME_ASSET`
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
- `MAINTENANCE_CHECKLIST_TEMPLATE_NOT_FOUND`
- `MAINTENANCE_CHECKLIST_TEMPLATE_CONFLICT`
- `MAINTENANCE_CHECKLIST_TEMPLATE_REQUIRED`
- `MAINTENANCE_CHECKLIST_TEMPLATE_ITEMS_REQUIRED`
- `MAINTENANCE_CHECKLIST_TEMPLATE_PERIOD_INVALID`
- `MAINTENANCE_CHECKLIST_EXECUTION_NOT_FOUND`
- `MAINTENANCE_CHECKLIST_EXECUTION_CONFLICT`
- `MAINTENANCE_CHECKLIST_EXECUTION_INVALID_STATUS`
- `MAINTENANCE_CHECKLIST_RESULT_REQUIRED`
- `MAINTENANCE_CHECKLIST_RESULT_INVALID`
- `MAINTENANCE_FINDING_NOT_FOUND`
- `MAINTENANCE_FINDING_REQUEST_CONFLICT`
- `MAINTENANCE_SYMPTOM_CODE_NOT_FOUND`
- `MAINTENANCE_SYMPTOM_CODE_CONFLICT`
- `MAINTENANCE_FAILURE_MODE_NOT_FOUND`
- `MAINTENANCE_FAILURE_MODE_CONFLICT`
- `MAINTENANCE_ROOT_CAUSE_CODE_NOT_FOUND`
- `MAINTENANCE_ROOT_CAUSE_CODE_CONFLICT`
- `MAINTENANCE_ASSET_FAILURE_NOT_FOUND`
- `MAINTENANCE_ASSET_FAILURE_CONFLICT`
- `MAINTENANCE_ASSET_FAILURE_TIME_INVALID`
- `MAINTENANCE_PART_USAGE_CONFLICT`
- `MAINTENANCE_PART_USAGE_INVALID_STATUS`
- `MAINTENANCE_LABOR_LOG_CONFLICT`
- `MAINTENANCE_LABOR_LOG_INVALID_STATUS`
- `MAINTENANCE_LABOR_LOG_TIME_INVALID`
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
