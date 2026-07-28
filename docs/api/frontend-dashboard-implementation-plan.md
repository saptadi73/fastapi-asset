# Frontend Dashboard Implementation Plan

Dokumen ini memecah dashboard dan report menjadi unit implementasi frontend yang
lebih operasional. Acuan data dan endpoint mengikuti backend yang tervalidasi
pada **Tuesday, July 28, 2026**.

Dokumen ini melengkapi:

- `docs/api/frontend-dashboard-report-catalog.md`
- `docs/api/frontend-functional-blueprint.md`
- `docs/api/frontend-page-endpoint-map.md`

## 1. Tujuan Implementasi

Dokumen ini membantu frontend menjawab 4 hal:

1. widget mana yang dibangun dulu
2. komponen visual apa yang dipakai
3. endpoint mana yang dipanggil
4. drilldown mana yang harus tersedia

## 2. Prioritas Halaman

Urutan yang paling efektif:

### Tier 1

- Executive Dashboard
- Maintenance Dashboard
- Tracking Verification Dashboard

### Tier 2

- Maintenance Cost Report
- Maintenance SLA Report
- Failure Analysis Report
- Entitlement Expiry Dashboard

### Tier 3

- Schedule Stability Dashboard
- Asset Lifecycle Risk Dashboard
- Maintenance Mix Dashboard

## 3. Executive Dashboard

Route yang disarankan:

- `/dashboard`

## 3.1 Layout

Komposisi:

- row 1: 6-8 KPI cards
- row 2: alert strip + outstanding work tables
- row 3: quick charts

## 3.2 Widget Specification

### Widget A. KPI Asset & Operations

Komponen:

- `SummaryCardGrid`

Isi:

- total asset aktif
- asset status abnormal
- transfer terbuka
- stocktake aktif
- request terbuka
- work order aktif

Source:

- `GET /api/v1/assets`
- `GET /api/v1/asset-transfers`
- `GET /api/v1/stocktakes`
- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/work-orders`

Jenis agregasi:

- frontend

Drilldown:

- click card -> buka list page terkait dengan filter preset

### Widget B. Maintenance Attention

Komponen:

- `AlertStrip`
- `MiniKpiStack`

Isi:

- overdue request count
- overdue work order count
- overdue schedule count

Source:

- `GET /api/v1/maintenance/reports/backlog`

Jenis agregasi:

- langsung dari backend

Drilldown:

- request list
- work order list
- schedule list

### Widget C. Verification Attention

Komponen:

- `TopAttentionTable`

Isi:

- unverified assets terlama

Source:

- `GET /api/v1/reports/unverified-assets?days_since_verified=30`

Drilldown:

- asset detail

### Widget D. Entitlement Warning

Komponen:

- `AlertListCard`

Isi:

- entitlement expiry dalam 30/60/90 hari

Source:

- `GET /api/v1/maintenance/entitlements/expiring?days_ahead=90`

Drilldown:

- warranty detail
- contract detail
- asset detail

## 3.3 Loading & Error Rules

- gunakan skeleton per widget, bukan spinner full page
- jika satu widget gagal, widget lain tetap render
- sediakan `retry` per widget

## 4. Maintenance Dashboard

Route yang disarankan:

- `/dashboard/maintenance`

## 4.1 Layout

Komposisi:

- hero KPI area
- tab chart/report
- 2 table bawah untuk operasional dan investigasi

## 4.2 Widget Specification

### Widget A. Backlog KPI

Komponen:

- `SummaryCardGrid`

Source:

- `GET /api/v1/maintenance/reports/backlog`

Field utama:

- `request_backlog_count`
- `overdue_request_count`
- `open_work_order_count`
- `overdue_work_order_count`
- `active_schedule_count`
- `overdue_schedule_count`

### Widget B. SLA Compliance

Komponen:

- `DualGaugeCard`
- `ComplianceBarCard`

Source:

- `GET /api/v1/maintenance/reports/sla`

Field utama:

- `response_sla_compliance_pct`
- `resolution_sla_compliance_pct`
- breach counts

Drilldown:

- report SLA page
- request list with breached status badge

### Widget C. Reliability KPI

Komponen:

- `KpiBand`

Source:

- `GET /api/v1/maintenance/reports/reliability`

Field utama:

- `total_downtime_minutes`
- `breakdown_work_order_count`
- `failure_count`
- `mtbf_hours`
- `mttr_hours`

### Widget D. Cost Composition

Komponen:

- `StackedCostBar`
- `DonutCostSplit`

Source:

- `GET /api/v1/maintenance/reports/cost?page=1&page_size=10`

Field utama:

- `actual_part_cost`
- `actual_labor_cost`
- `actual_vendor_cost`
- `total_actual_cost`

### Widget E. Failure Analysis Snapshot

Komponen:

- `BucketBarChart`
- `TopListCard`

Source:

- `GET /api/v1/maintenance/reports/failure-analysis`

Field utama:

- failure mode buckets
- root cause buckets
- top assets by failure count

### Widget F. Open Work Queue

Komponen:

- `CompactTable`

Source:

- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/work-orders`

Isi:

- request prioritas tertinggi
- work order aktif terbaru

## 5. Tracking Verification Dashboard

Route yang disarankan:

- `/dashboard/tracking`

## 5.1 Widget Specification

### Widget A. Verification KPI

Komponen:

- `SummaryCardGrid`

Source:

- `GET /api/v1/reports/unverified-assets`
- `GET /api/v1/reports/location-discrepancies`
- `GET /api/v1/reports/missing-assets`

Isi:

- unverified asset count
- discrepancy unresolved count
- missing asset count

### Widget B. Verification Aging

Komponen:

- `BucketCardGroup`

Source:

- `GET /api/v1/reports/unverified-assets?days_since_verified=30`
- `GET /api/v1/reports/unverified-assets?days_since_verified=60`
- `GET /api/v1/reports/unverified-assets?days_since_verified=90`

Catatan:

- bisa dibangun bertahap dengan 3 query kecil

### Widget C. Location Discrepancy Table

Komponen:

- `DataTable`

Source:

- `GET /api/v1/reports/location-discrepancies`

Kolom:

- asset
- expected location
- observed location
- verified_at
- resolution_status

### Widget D. Missing Asset Table

Komponen:

- `DataTable`

Source:

- `GET /api/v1/reports/missing-assets`

Kolom:

- asset
- stocktake session
- location
- result_type
- resolution_status

## 6. Maintenance Cost Report Page

Route yang disarankan:

- `/reports/maintenance-cost`

## 6.1 Header Filters

Komponen:

- `DateRangeFilter`
- `AssetLookup`
- `MaintenanceTypeSelect`

Query:

- `asset_id`
- `maintenance_type`
- `date_from`
- `date_to`
- `sort`
- `order`

## 6.2 Main Content

Komposisi:

- summary row
- cost split donut
- sortable table

Widget:

- `CostSummaryCards`
- `CostSplitDonut`
- `MaintenanceCostTable`

## 7. Maintenance SLA Report Page

Route yang disarankan:

- `/reports/maintenance-sla`

Komposisi:

- 2 compliance cards
- breach summary
- period filter

Widget:

- `SlaComplianceCards`
- `BreachSummaryCard`
- `DateRangeFilter`

Source:

- `GET /api/v1/maintenance/reports/sla`

## 8. Failure Analysis Report Page

Route yang disarankan:

- `/reports/failure-analysis`

## 8.1 Filters

- `asset_id`
- `failure_mode_id`
- `root_cause_code_id`
- `date_from`
- `date_to`

## 8.2 Visual Blocks

- `FailureModeBarChart`
- `RootCauseBarChart`
- `TopFailedAssetsTable`
- `RepeatFailureInsightsCard`

Source:

- `GET /api/v1/maintenance/reports/failure-analysis`

## 9. Entitlement Expiry Dashboard

Route yang disarankan:

- `/reports/entitlement-expiry`

Widget:

- `ExpirySummaryCards`
- `ExpiryTimelineTable`
- `ProviderBreakdownList`

Source:

- `GET /api/v1/maintenance/entitlements/expiring`

Recommended filters:

- `days_ahead`: 30 / 60 / 90 / 120

## 10. Schedule Stability Dashboard

Route yang disarankan:

- `/reports/schedule-stability`

Catatan:

- ini sangat bernilai walaupun belum ada endpoint khusus

## 10.1 Build Strategy

Step awal:

1. panggil `GET /api/v1/maintenance/schedules`
2. ambil schedule yang `reschedule_count > 0`
3. lazy load event history hanya untuk row yang dibuka user

## 10.2 Widgets

- `ScheduleStatusDistribution`
- `ScheduleSourceDistribution`
- `RescheduleReasonTable`
- `MostRescheduledSchedules`

Source:

- `GET /api/v1/maintenance/schedules`
- `GET /api/v1/maintenance/schedules/{schedule_id}/events`

## 11. Asset Lifecycle Risk Dashboard

Route yang disarankan:

- `/reports/asset-lifecycle-risk`

## 11.1 Widget Strategy

Karena belum ada endpoint agregat khusus, build bertahap:

1. gunakan asset list untuk daftar kandidat
2. buka lifecycle review saat user drilldown atau expand row

Widget:

- `RiskAttentionList`
- `ReplacementRecommendationTable`
- `SupportEndWatchlist`

Source:

- `GET /api/v1/assets`
- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`

## 12. Reusable Frontend Components

Komponen yang paling berguna untuk seluruh dashboard/report:

- `SummaryCard`
- `SummaryCardGrid`
- `AlertStrip`
- `KpiBand`
- `CompactTable`
- `DataTable`
- `DateRangeFilter`
- `StatusChip`
- `EmptyStateCard`
- `WidgetErrorCard`
- `WidgetShell`
- `DrilldownLink`

## 13. Query and State Strategy

Prinsip implementasi:

- satu query per widget besar
- cache list master untuk dropdown filter
- gunakan lazy fetch untuk detail atau event history
- jangan blokir satu halaman jika satu widget gagal

Recommended query keys:

- `dashboard-executive`
- `dashboard-maintenance-backlog`
- `dashboard-maintenance-sla`
- `dashboard-maintenance-reliability`
- `dashboard-maintenance-cost`
- `dashboard-tracking-discrepancies`
- `report-failure-analysis`
- `report-entitlement-expiry`

## 14. Empty State Rules

Jika data kosong:

- tampilkan card kosong yang menjelaskan bahwa belum ada data operasional
- tetap render filter dan struktur chart/table
- hindari dashboard kosong total tanpa konteks

Contoh:

- `Belum ada work order closed pada periode ini.`
- `Belum ada entitlement yang akan berakhir dalam 90 hari ke depan.`
- `Belum ada discrepancy stocktake yang belum diselesaikan.`

## 15. Sprint Frontend yang Disarankan

### Sprint A

- Executive Dashboard
- Maintenance Dashboard
- Tracking Verification Dashboard

### Sprint B

- Cost Report
- SLA Report
- Failure Analysis Report

### Sprint C

- Entitlement Expiry Dashboard
- Schedule Stability Dashboard
- Lifecycle Risk Dashboard
