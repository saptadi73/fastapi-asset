# Frontend Form Simplification Guide

Dokumen ini mengidentifikasi field-field backend yang sebaiknya tidak selalu
ditampilkan sebagai input manual di frontend. Tujuannya agar form lebih
sederhana, lebih kaya interaksi, dan lebih aman terhadap kesalahan user.

Tanggal acuan: **Tuesday, July 28, 2026**.

Dokumen ini melengkapi:

- `docs/api/frontend-api-reference.md`
- `docs/api/frontend-functional-blueprint.md`
- `docs/api/frontend-page-endpoint-map.md`

## 1. Prinsip Umum

Kelompok field yang sebaiknya diperlakukan berbeda di frontend:

### 1.1 Hidden / Auto-Filled

Field ini sebaiknya tidak dijadikan input manual biasa:

- `created_by`
- `updated_by`
- `actor_id`
- `approved_by`
- `requested_by`
- `scanned_by`
- `captured_by`
- `uploaded_by`
- `deleted_by`

Alasan:

- route backend saat ini banyak yang sudah mengisi field audit dari bearer token;
- jika field audit tetap ditampilkan, UX lebih berat dan rawan mismatch.

### 1.2 Dropdown / Lookup

Field referensi yang sebaiknya memakai dropdown, autocomplete, atau lookup:

- seluruh field `*_id` yang menunjuk master data
- enum seperti `status`, `type`, `role`, `priority`, `condition`

Alasan:

- mengurangi typo;
- menjaga konsistensi dengan business rule backend;
- memudahkan user menemukan pilihan yang valid.

### 1.3 Conditional Fields

Field ini sebaiknya baru muncul bila toggle atau pilihan tertentu aktif:

- tanggal akhir bila mode sementara / recurring / renewable aktif
- vendor field bila mode eksekusi vendor dipilih
- downtime field bila asset benar-benar berhenti
- rule JSON bila trigger plan tertentu dipilih

### 1.4 Advanced Section

Field-field teknis atau jarang dipakai sebaiknya dipindahkan ke area:

- `Advanced`
- `Optional`
- `Integration / SAP`

Tujuannya agar form default tetap pendek.

## 2. Global Rules

### 2.1 Jangan tampilkan manual

Sebaiknya hidden atau dibentuk sistem:

- audit fields: `created_by`, `updated_by`, `actor_id`, `scanned_by`,
  `uploaded_by`, `captured_by`, `deleted_by`
- file storage internals: `storage_provider`, `storage_bucket`,
  `storage_object_key`, `checksum_sha256`
- metadata teknis integrasi SAP kecuali user memang sedang ada di menu
  integrasi/admin

### 2.2 Gunakan default UI

Default yang disarankan:

- `is_active = true`
- `is_primary = false`
- `auto_renewal = false`
- `requires_verification = true`
- `is_asset_stopped = false`
- `safety_impact = false`
- `environmental_impact = false`
- `production_impact = false`

Frontend sebaiknya tampilkan ini sebagai switch/toggle, bukan input teks.

## 3. Asset Registry

### 3.1 Asset Create / Edit

#### Tampilkan di form utama

- `asset_code`
- `asset_name`
- `asset_category_id`
- `asset_class_id`
- `asset_type`
- `asset_status`
- `condition_status`
- `current_location_id`
- `serial_number`
- `brand`
- `model`
- `manufacturer_id`
- `in_service_date`

#### Jadikan dropdown / lookup

- `asset_category_id`
- `asset_class_id`
- `parent_asset_id`
- `manufacturer_id`
- `company_id`
- `branch_id`
- `current_location_id`
- `current_primary_custodian_id`
- `asset_type`
- `asset_status`
- `condition_status`
- `tracking_status`
- `replacement_strategy`
- `replacement_priority`

#### Pindahkan ke section `Advanced`

- `criticality_level`
- `barcode`
- `qr_code`
- `tag_number`
- `last_verified_at`
- `last_verified_location_id`
- `retirement_date`
- `expected_replacement_date`
- `support_end_date`
- `vendor_end_of_sale_date`
- `vendor_end_of_support_date`
- `estimated_replacement_cost`
- `replacement_budget_year`
- `next_review_date`
- `sap_asset_code`
- `sap_item_code`

#### Hidden / auto

- `created_by`
- `updated_by`

### 3.2 Asset Attribute Values

Jangan tampilkan semua field nilai sekaligus.

Gunakan renderer berdasarkan `data_type`:

- `TEXT` -> text input
- `NUMBER` -> numeric input
- `DATE` -> date picker
- `BOOLEAN` -> switch
- `JSON` -> key-value editor atau textarea JSON

Field yang tetap hidden:

- `value_text`, `value_number`, `value_date`, `value_boolean`, `value_json`
  yang tidak sesuai `data_type`

### 3.3 Asset Ownership

#### Gunakan segmented choice untuk `owner_type`

- `COMPANY`
- `PARTNER`

#### Conditional

- bila `owner_type = PARTNER`, tampilkan `owner_partner_id`
- bila `owner_type = COMPANY`, tampilkan `owner_company_id`

#### Optional / advanced

- `source_reference`
- `notes`
- `effective_to`

### 3.4 Asset Transfer

#### Form utama

- `transfer_number`
- `transfer_date`
- `transfer_type`
- `movement_purpose`
- `to_location_id`
- `items`

#### Conditional

- `expected_return_at` hanya bila `is_permanent = false`
- `from_location_id` bisa otomatis diambil dari asset atau current context bila
  transfer dimulai dari asset detail
- `from_department_id` dan `to_department_id` cukup tampil bila organisasi
  memang memakai perpindahan antar departemen

#### Item transfer

Gunakan tabel item dengan kolom:

- `asset_id`
- `new_custodian_id`
- `handover_condition`
- `notes`

Jangan tampilkan manual kecuali memang ada use case scan:

- `dispatch_scan_event_id`
- `receipt_scan_event_id`
- `item_status`

#### Hidden / auto

- `requested_by`
- `actor_id` pada action `submit`, `approve`, `complete`

### 3.5 Asset Status / Location / Assignment / Component

#### Gunakan action drawer kecil

Bukan form halaman penuh.

#### Dropdown

- `new_status`
- `new_condition`
- `assignment_type`
- `component_action_type`

#### Conditional

- `return` assignment cukup tombol aksi, bukan minta isi banyak field
- component replace sebaiknya flow 2 langkah:
  pilih komponen lama -> pilih komponen pengganti

#### Hidden / auto

- `recorded_by`
- `changed_by`

## 4. Business Partners

### 4.1 Business Partner Create

#### Form utama

- `partner_code`
- `partner_name`
- `email`
- `phone`
- `address`

#### Optional / advanced

- `tax_number`
- `sap_card_code`
- `is_active`

#### Roles

`roles` sebaiknya bukan JSON mentah.

Gunakan:

- multi-select role chips
- optional drawer untuk `valid_from` dan `valid_to`

## 5. Attachments

### 5.1 Jangan jadikan storage metadata sebagai input user biasa

Untuk frontend normal, user sebaiknya hanya melihat:

- pilih file
- title
- description
- category
- visibility
- is_primary

Field yang sebaiknya tidak diinput manual oleh user akhir:

- `storage_provider`
- `storage_bucket`
- `storage_object_key`
- `checksum_sha256`
- `mime_type` bila bisa dibaca otomatis dari file
- `extension` bila bisa dibaca otomatis dari nama file
- `size_bytes` bila bisa dibaca otomatis
- `uploaded_by`
- `created_by`

### 5.2 Conditional metadata

Tampilkan hanya bila user klik `Add capture metadata`:

- `captured_at`
- `captured_by`
- `latitude`
- `longitude`

### 5.3 Versioning UI

`FileVersionCreate` sebaiknya cukup tampilkan:

- pilih file baru
- `change_notes`

Jangan tampilkan field storage mentah bila frontend nanti memakai upload
adapter sendiri.

## 6. Tracking & Stocktake

### 6.1 Scan Event

Untuk UI operator, form idealnya sangat pendek:

- scan / paste `raw_tag_uid`
- pilih `scan_type`
- `scanned_location_id`
- `scanned_at`

#### Hidden / auto

- `event_uid` dibuat client otomatis
- `scan_source` default `API`
- `received_at` bisa otomatis `now`
- `scanned_by` dari token

#### Optional / advanced

- `device_id`
- `latitude`
- `longitude`
- `gps_accuracy_meters`
- `transfer_id`
- `stocktake_session_id`
- `metadata`

### 6.2 Stocktake Session

#### Form utama

- `session_number`
- `location_id`
- `planned_start_at`

#### Optional

- `planned_end_at`
- `notes`

#### Hidden / auto

- `created_by`

#### Conditional

- `scope_type` boleh disembunyikan bila saat ini mayoritas flow memakai
  `LOCATION`

### 6.3 Stocktake Actions

Action payload seperti start/complete/approve cukup pakai:

- tombol aksi
- optional notes
- `acted_at` bisa otomatis `now`

Jangan minta user pilih `actor_id`.

## 7. Leases

### 7.1 Lease Contract

#### Form utama

- `contract_number`
- `lessor_partner_id`
- `lease_type`
- `accounting_treatment`
- `start_date`
- `end_date`
- `billing_frequency`
- `payment_amount`
- `currency_code`
- `status`

#### Dropdown / lookup

- `lessor_partner_id`
- `lease_type`
- `accounting_treatment`
- `billing_frequency`
- `currency_code`
- `status`

#### Optional / advanced

- `lessee_company_id`
- `extension_option_end_date`
- `deposit_amount`
- `purchase_option_amount`
- `notice_period_days`

#### Conditional

- `notice_period_days` hanya bila `auto_renewal = true`
- `extension_option_end_date` hanya bila ada extension option

#### Switch group

- `auto_renewal`
- `maintenance_included`
- `insurance_included`
- `tax_included`

### 7.2 Lease Contract Asset

#### Form utama

- `asset_id`
- `lease_start_date`
- `lease_end_date`

#### Optional

- `monthly_amount`
- `allocation_percentage`
- `return_condition`
- `returned_at`

## 8. Software Licenses

### 8.1 Software Product

#### Form utama

- `product_code`
- `product_name`
- `product_type`

#### Conditional

- `publisher_partner_id` bila publisher dipilih dari partner master
- `publisher_name` bila publisher diisi bebas

#### Optional

- `version`
- `edition`

### 8.2 Software License

#### Form utama

- `software_product_id`
- `license_model`
- `license_metric`
- `license_quantity`
- `status`

#### Optional

- `license_number`
- `purchase_date`
- `activation_date`
- `start_date`
- `expiry_date`
- `renewal_type`
- `subscription_cost`
- `currency_code`
- `supplier_id`
- `maintenance_contract_id`
- `support_end_date`
- `update_entitlement_end_date`

#### Conditional

- `renewal_notice_days` hanya bila `expiry_date` atau `auto_renewal` diisi
- `currency_code` hanya bila `subscription_cost` diisi

#### Jangan tampilkan biasa

- `license_key_encrypted` sebaiknya disembunyikan di balik tombol
  `Add secret/license key`

### 8.3 Software License Assignment

Gunakan segmented choice:

- assign ke `Asset`
- assign ke `Employee`

#### Conditional

- bila target `Asset`, tampilkan `asset_id`
- bila target `Employee`, tampilkan `employee_id`

Jangan tampilkan kedua field sekaligus.

## 9. Maintenance Master

### 9.1 Priority

#### Form utama

- `code`
- `name`
- `severity_level`

#### Optional

- `default_response_minutes`
- `default_resolution_minutes`
- `escalation_after_minutes`
- `color_code`

#### Switch

- `is_emergency`
- `is_active`

### 9.2 Team

#### Form utama

- `company_id`
- `team_code`
- `team_name`
- `team_type`

#### Optional

- `department_id`
- `supervisor_employee_id`
- `default_location_id`

### 9.3 Skill / Employee Skill

#### Skill

Form utama:

- `skill_code`
- `skill_name`

Optional:

- `certification_required`

#### Employee Skill

Form utama:

- `maintenance_skill_id`

Conditional:

- `certificate_number` bila skill butuh sertifikasi

Optional:

- `proficiency_level`
- `valid_from`
- `valid_to`

## 10. Maintenance Entitlement

### 10.1 Contract

#### Form utama

- `contract_number`
- `contract_name`
- `vendor_partner_id`
- `contract_type`
- `start_date`
- `end_date`
- `status`

#### Switch group

- `preventive_maintenance_included`
- `corrective_maintenance_included`
- `spare_parts_included`
- `labor_included`
- `onsite_support_included`
- `remote_support_included`

#### Optional / advanced

- `response_time_hours`
- `resolution_time_hours`
- `contract_value`
- `currency_code`
- `billing_frequency`
- `notice_period_days`
- `sap_purchase_contract_reference`

#### Conditional

- `notice_period_days` hanya bila `auto_renewal = true`
- `currency_code` hanya bila `contract_value > 0`

### 10.2 Contract Coverage Asset

#### Form utama

- `asset_id`
- `coverage_start_date`
- `coverage_end_date`
- `coverage_level`

#### Optional

- `annual_allocation_amount`
- `specific_exclusions`

### 10.3 Warranty

#### Form utama

- `asset_id`
- `warranty_type`
- `coverage_start_date`
- `coverage_end_date`
- `status`

#### Optional

- `warranty_provider_partner_id`
- `warranty_number`
- `claim_deadline_date`
- `coverage_scope`
- `notes`

### 10.4 Warranty Claim

#### Form utama

- `claim_number`
- `claim_date`
- `problem_description`
- `claim_status`

#### Conditional

- `resolved_at` dan `resolution_description` hanya bila status claim resolved/closed
- `replacement_asset_id` hanya bila ada penggantian unit

#### Optional

- `cost_covered`
- `cost_not_covered`

## 11. Maintenance Request

### 11.1 Request Create

#### Form utama

- `request_number`
- `company_id`
- `asset_id`
- `request_type`
- `source_type`
- `reported_at`
- `title`
- `problem_description`
- `priority_id`

#### Toggle-driven fields

- bila `is_asset_stopped = true`, tampilkan `downtime_started_at`
- bila `production_impact = true`, tampilkan impact badge atau note

#### Optional

- `reported_by_name`
- `asset_location_id`
- `operating_condition`
- `requested_vendor_partner_id`

#### Advanced entitlement

Sebaiknya tampil di drawer/accordion:

- `maintenance_contract_id`
- `warranty_id`
- `required_response_at`
- `required_resolution_at`

#### Hidden / auto

- `created_by`
- `updated_by`
- `requested_by_employee_id` bila bisa diambil dari user profile
- `parent_request_id` untuk flow normal single request

### 11.2 Request Batch

#### Form header

- `company_id`
- `request_type`
- `source_type`
- `reported_at`
- `priority_id`

#### Item rows

- `request_number`
- `asset_id`
- `title`
- `problem_description`

#### Optional item fields

- `asset_location_id`
- `operating_condition`
- `requested_vendor_partner_id`
- `maintenance_contract_id`
- `warranty_id`

#### Hidden / auto

- `created_by`
- `updated_by`
- `requested_by_employee_id`

### 11.3 Request Actions

Payload `submit`, `approve`, `reject` sebaiknya jadi tombol aksi saja.

Yang user isi hanya:

- `notes` bila perlu
- `rejection_reason` untuk reject

Field `actor_id` dan `acted_at` sebaiknya tidak jadi input eksplisit.

### 11.4 Triage

Triage sebaiknya tampil sebagai form kontekstual, bukan seluruh request diulang.

Tampilkan hanya:

- `priority_id`
- `asset_location_id`
- `operating_condition`
- `maintenance_contract_id`
- `warranty_id`
- `requested_vendor_partner_id`
- `required_response_at`
- `required_resolution_at`

## 12. Maintenance Work Order

### 12.1 Work Order Create / Convert

#### Form utama

- `work_order_number`
- `maintenance_type`
- `execution_mode`
- `scope_of_work`

#### Dropdown / lookup

- `priority_id`
- `vendor_partner_id`
- `maintenance_type`
- `execution_mode`

#### Conditional

- `vendor_partner_id` hanya bila `execution_mode = VENDOR` atau `HYBRID`
- `planned_end_at` boleh muncul setelah `planned_start_at` terisi

#### Optional

- `planned_start_at`
- `planned_end_at`
- `asset_condition_before`

#### Advanced

- `requires_shutdown`
- `requires_permit`
- `requires_verification`
- `estimated_labor_cost`
- `estimated_part_cost`
- `estimated_vendor_cost`
- `currency_code`

#### Hidden / auto

- `created_by`
- `updated_by`
- `company_id` dan `asset_id` bila work order dibuat dari request/asset context

### 12.2 Assignment

#### Form utama

- `employee_id`
- `assignment_role`

#### Optional

- `planned_minutes`
- `accepted_at`

#### Hidden / auto

- `actor_id`
- `acted_at`

### 12.3 Complete / Verify / Hold / Resume / Cancel / Close

Sebagian besar sebaiknya berupa action modal kecil.

#### Complete

Tampilkan:

- `completion_summary`
- `asset_condition_after`
- `resolution_code`
- `actual_labor_cost`
- `actual_part_cost`
- `actual_vendor_cost`

#### Verify

Hanya tombol + optional notes bila nanti dibutuhkan.

#### Hidden / auto

- `actor_id`
- `acted_at`

### 12.4 Required Skill

#### Form utama

- `maintenance_skill_id`

#### Optional

- `minimum_proficiency_level`
- `notes`

#### Conditional

- `certification_required` sebaiknya default mengikuti master skill,
  cukup tampil sebagai override toggle

## 13. Maintenance Execution

### 13.1 Part Requirement

#### Form utama

- `part_item_id`
- `required_quantity`
- `unit_of_measure`

#### Optional

- `reserved_quantity`
- `is_critical`
- `notes`

#### Advanced

- `requirement_status`

### 13.2 Vendor Personnel

#### Form utama

- `vendor_partner_id`
- `person_name`

#### Optional

- `contact_phone`
- `technician_reference`
- `check_in_at`
- `check_out_at`

### 13.3 Part Usage

#### Form utama

- `part_item_id`
- `quantity`
- `usage_type`
- `used_at`

#### Conditional

- `currency_code` bila `unit_cost` diisi
- `removed_component_asset_id` dan `installed_component_asset_id` hanya untuk
  use case replacement / component swap
- `serial_number` hanya untuk item serial-managed

#### Optional / advanced

- `unit_cost`
- `used_by_employee_id`
- `sap_inventory_doc_entry`
- `sap_inventory_doc_num`

### 13.4 Labor Log

#### Form utama

- `employee_id`
- `started_at`
- `activity_type`

#### Optional

- `ended_at`
- `duration_minutes`
- `hourly_rate`
- `labor_cost`
- `notes`

### 13.5 Downtime

#### Form utama

- `downtime_type`
- `started_at`
- `reason`

#### Optional

- `ended_at`
- `duration_minutes`
- `production_loss_quantity`
- `unit_of_measure`

#### Conditional

- `unit_of_measure` hanya bila `production_loss_quantity` diisi

### 13.6 Failure / RCA

#### Form utama

- `failure_number`
- `detected_at`
- `failure_description`
- `failure_severity`

#### Dropdown / lookup

- `failure_mode_id`
- `symptom_code_id`
- `root_cause_code_id`
- `status`

#### Optional

- `asset_condition_before`
- `asset_condition_after`
- `temporary_action`
- `root_cause_description`
- `corrective_action`
- `preventive_action`
- `failure_started_at`
- `failure_ended_at`
- `downtime_minutes`

#### Switch

- `caused_shutdown`
- `safety_incident`
- `repeat_failure`

#### Hidden / auto

- `created_by`
- `detected_by_employee_id` bisa default current user

## 14. Maintenance Schedule & Plan

### 14.1 Manual Schedule

#### Form utama

- `schedule_number`
- `asset_id`
- `schedule_source`
- `scheduled_start_at`
- `scheduled_end_at`

#### Optional

- `maintenance_plan_id`
- `maintenance_request_id`
- `work_order_id`
- `maintenance_team_id`
- `vendor_partner_id`
- `maintenance_contract_id`

#### Hidden / auto

- `created_by`
- `created_at`

### 14.2 Reschedule

Jadikan modal kecil berisi:

- `scheduled_start_at`
- `scheduled_end_at`
- `reschedule_reason`

Jangan minta `actor_id` manual.

### 14.3 Plan Create

#### Form utama

- `plan_code`
- `plan_name`
- `maintenance_type`
- `trigger_type`
- `default_priority_id`

#### Target scope

Gunakan pilihan:

- `Single Asset`
- `Asset Category`

Conditional:

- bila `Single Asset`, tampilkan `asset_id`
- bila `Asset Category`, tampilkan `asset_category_id`

#### Trigger-driven fields

- `CALENDAR`:
  - `calendar_interval_value`
  - `calendar_interval_unit`
  - `next_due_date`
- `METER`:
  - `meter_id`
  - `meter_interval`
  - `next_due_meter_value`
- `CALENDAR_OR_METER` / `CALENDAR_AND_METER`:
  - gabungkan field calendar + meter
- `CONDITION`:
  - tampilkan rule builder sederhana untuk `condition_rule`
- `PREDICTIVE`:
  - tampilkan rule builder sederhana untuk `predictive_rule`
- `MANUAL`:
  - sembunyikan field rule due

#### Optional

- `default_team_id`
- `default_vendor_partner_id`
- `maintenance_contract_id`
- `checklist_template_id`
- `estimated_duration_minutes`
- `lead_time_days`
- `effective_to`

#### Switch

- `auto_create_request`
- `auto_create_work_order`
- `requires_approval`
- `is_active`

### 14.4 Plan Generate

#### Form utama

- `scheduled_start_at`

#### Optional

- `schedule_prefix`
- `create_work_orders`
- `generation_reason`

#### Conditional by trigger

- meter-based plan -> tampilkan `meter_reading_value`
- condition-based plan -> tampilkan `condition_snapshot`
- predictive plan -> tampilkan `predictive_snapshot`

#### Hidden / auto

- `created_by`
- `trigger_evaluated_at` bisa default `now`

## 15. Checklist & Findings

### 15.1 Checklist Template

#### Form utama

- `template_code`
- `template_name`

#### Optional

- `asset_category_id`
- `maintenance_type`
- `effective_to`

#### Item editor

Untuk tiap item, tampilkan:

- `sequence_no`
- `item_code`
- `instruction`
- `response_type`
- `is_required`

Conditional:

- `normal_min_value` dan `normal_max_value` hanya untuk numeric
- `unit_of_measure` hanya untuk numeric/meter
- `failure_response_rule` sebagai dropdown

### 15.2 Checklist Execution Start

#### Form utama

- `performed_by_employee_id`

#### Optional

- `checklist_template_id` bila tidak otomatis ikut dari work order
- `started_at` bisa default `now`

### 15.3 Checklist Result Submit

Frontend jangan tampilkan semua field hasil sekaligus.

Gunakan renderer berdasarkan tipe item checklist:

- pass/fail -> radio
- yes/no -> radio
- numeric -> number input
- text -> textarea
- photo -> attachment uploader
- meter reading -> numeric + meter reference bila nanti tersedia

Field finding lanjutan seperti:

- `finding_type`
- `finding_severity`
- `finding_description`
- `recommended_action`
- `requires_follow_up`
- `requires_asset_shutdown`
- `follow_up_due_date`

sebaiknya muncul hanya bila hasil abnormal.

### 15.4 Finding to Request

Saat membuat request dari finding, form utama cukup:

- `request_number`
- `priority_id`
- `reported_at`
- `title`
- `problem_description`

Optional:

- `requested_vendor_partner_id`
- `required_response_at`
- `required_resolution_at`
- `submit`

Hidden / auto:

- `created_by`
- `updated_by`

## 16. Ringkasan Paling Penting

Jika frontend ingin cepat mulai dengan UX yang lebih bersih, lakukan 5 aturan ini
lebih dulu:

1. Sembunyikan seluruh audit field dari form user.
2. Semua `*_id` jadikan dropdown/autocomplete, bukan text input.
3. Pakai toggle untuk field opsional seperti downtime, auto-renewal,
   vendor execution, entitlement, dan approval.
4. Pindahkan field SAP, geolocation, financial detail, dan technical storage ke
   section `Advanced`.
5. Bangun form dinamis untuk `asset attributes`, `maintenance plan trigger`,
   dan `checklist results`, bukan form statis semua field.
