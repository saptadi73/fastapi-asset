# Frontend Dashboard & Report Catalog

Dokumen ini memperkaya ide dashboard dan report yang bisa dibangun di sisi
frontend berdasarkan backend yang sudah tersedia pada **Tuesday, July 28, 2026**.

Tujuan:

- membantu frontend membangun dashboard yang lebih kaya tanpa menunggu endpoint
  baru;
- memisahkan report yang sudah bisa dibentuk dari API saat ini vs report yang
  nanti lebih baik dipindahkan ke backend khusus;
- memberi ide visualisasi, drilldown, dan menu report yang lebih bernilai.

Referensi pendukung:

- `docs/api/frontend-functional-blueprint.md`
- `docs/api/frontend-page-endpoint-map.md`
- `docs/api/frontend-api-reference.md`
- `artifacts/frontend_endpoint_samples.json`

## 1. Prinsip Penyusunan Report

Kelompok report yang paling masuk akal:

1. `Operational Dashboard`
2. `Maintenance Control Tower`
3. `Asset Health & Lifecycle`
4. `Tracking & Verification`
5. `Cost & SLA Governance`
6. `Reliability & Failure Analysis`

Kategori implementasi:

- `langsung jadi`: bisa dibangun dari satu endpoint report/list yang sudah ada
- `frontend-derived`: bisa dibangun dengan menggabungkan beberapa endpoint yang
  sudah ada
- `backend-later`: sebaiknya nanti dibuat endpoint khusus agar lebih efisien

## 2. Executive Dashboard

Halaman ini cocok sebagai landing page manajerial.

### 2.1 KPI Cards

Widget:

- total asset aktif
- total asset dengan status tidak normal
- request maintenance terbuka
- work order aktif
- backlog overdue
- asset belum diverifikasi
- kontrak/warranty mendekati expiry
- stocktake aktif

Sumber data:

- `GET /api/v1/assets`
- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/work-orders`
- `GET /api/v1/maintenance/reports/backlog`
- `GET /api/v1/reports/unverified-assets`
- `GET /api/v1/maintenance/entitlements/expiring`
- `GET /api/v1/stocktakes`

Kategori:

- `frontend-derived`

### 2.2 Alert Strip

Isi alert prioritas tinggi:

- SLA breach count
- request breakdown yang belum jadi work order
- asset critical condition
- warranty/contract expiry dalam 30 hari
- missing asset dari stocktake

Sumber data:

- `GET /api/v1/maintenance/reports/sla`
- `GET /api/v1/maintenance/requests`
- `GET /api/v1/assets`
- `GET /api/v1/maintenance/entitlements/expiring`
- `GET /api/v1/reports/missing-assets`

Kategori:

- `frontend-derived`

## 3. Maintenance Control Tower

Halaman ini cocok untuk planner, supervisor, dan admin maintenance.

### 3.1 Backlog Command Center

Widget:

- request backlog count
- overdue request count
- open work order count
- overdue work order count
- active schedule count
- overdue schedule count

Sumber data:

- `GET /api/v1/maintenance/reports/backlog`

Kategori:

- `langsung jadi`

Visual:

- 6 KPI cards
- heat indicator merah/kuning/hijau
- drilldown ke request list, work order list, schedule list

### 3.2 Schedule Risk Panel

Widget:

- schedule `PLANNED` vs `CONFIRMED` vs `POSTPONED`
- schedule dengan `reschedule_count > 0`
- daftar schedule dengan event `RESCHEDULED`
- distribusi source:
  `PREVENTIVE_PLAN`, `METER_TRIGGER`, `CONDITION_TRIGGER`, `PREDICTIVE_TRIGGER`

Sumber data:

- `GET /api/v1/maintenance/schedules`
- `GET /api/v1/maintenance/schedules/{schedule_id}/events`

Kategori:

- `frontend-derived`

Nilai tambah:

- menonjolkan schedule yang tampak tidak stabil
- memberi bukti audit perubahan planning

### 3.3 Plan Trigger Monitor

Widget:

- jumlah plan by `trigger_type`
- due generation terbaru by `schedule_source`
- plan predictive / condition / meter yang paling aktif

Sumber data:

- `GET /api/v1/maintenance/plans`
- `GET /api/v1/maintenance/schedules`

Kategori:

- `frontend-derived`

### 3.4 Request-to-Work-Order Funnel

Widget:

- jumlah request `DRAFT`, `SUBMITTED`, `TRIAGE`, `APPROVED`
- jumlah request yang sudah menjadi work order
- conversion lag sederhana berdasarkan `reported_at` vs `created_at work order`

Sumber data:

- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/work-orders`

Kategori:

- `frontend-derived`

Catatan:

- funnel awal ini sudah cukup berguna meskipun belum ada endpoint analytics
  khusus

## 4. SLA & Entitlement Dashboard

### 4.1 SLA Compliance Board

Widget:

- response SLA target count
- response SLA met count
- response SLA breached count
- response SLA compliance %
- resolution SLA target count
- resolution SLA met count
- resolution SLA breached count
- resolution SLA compliance %

Sumber data:

- `GET /api/v1/maintenance/reports/sla`

Kategori:

- `langsung jadi`

### 4.2 Request SLA Audit

Widget:

- daftar request dengan snapshot SLA
- SLA source: contract / warranty / fallback
- recommended execution mode internal vs vendor
- escalation status

Sumber data:

- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/requests/{request_id}/sla-snapshots`

Kategori:

- `frontend-derived`

### 4.3 Entitlement Expiry Cockpit

Widget:

- total warranty expiring
- total contract coverage expiring
- daftar top 10 entitlement paling dekat expiry
- group by provider/vendor

Sumber data:

- `GET /api/v1/maintenance/entitlements/expiring`

Kategori:

- `langsung jadi`

## 5. Cost Dashboard

### 5.1 Cost Summary

Widget:

- total actual part cost
- total actual labor cost
- total actual vendor cost
- total actual cost
- top 10 work order by cost

Sumber data:

- `GET /api/v1/maintenance/reports/cost`

Kategori:

- `langsung jadi`

Visual:

- stacked bar per work order
- donut split labor/part/vendor
- sortable cost table

### 5.2 Cost by Maintenance Type

Widget:

- total cost preventive
- total cost corrective
- total cost breakdown
- total cost predictive

Sumber data:

- `GET /api/v1/maintenance/reports/cost?maintenance_type=...`

Kategori:

- `frontend-derived`

### 5.3 Cost by Asset

Widget:

- top expensive assets
- total work order count per asset
- total cost accumulation per asset

Sumber data:

- `GET /api/v1/maintenance/reports/cost`

Kategori:

- `frontend-derived`

Catatan:

- cocok untuk tab tambahan di asset detail

## 6. Reliability Dashboard

### 6.1 Reliability KPI

Widget:

- total downtime minutes
- breakdown count
- failure count
- MTTR
- MTBF

Sumber data:

- `GET /api/v1/maintenance/reports/reliability`

Kategori:

- `langsung jadi`

### 6.2 Failure Concentration

Widget:

- top failure mode
- top root cause
- top asset by failure count
- asset with highest downtime

Sumber data:

- `GET /api/v1/maintenance/reports/failure-analysis`

Kategori:

- `langsung jadi`

### 6.3 Failure Investigation Board

Widget:

- filter by asset
- filter by failure mode
- filter by root cause
- daftar case failure dan trend severity

Sumber data:

- `GET /api/v1/maintenance/reports/failure-analysis`
- `GET /api/v1/maintenance/failures`

Kategori:

- `frontend-derived`

## 7. Asset Health & Lifecycle Dashboard

### 7.1 Lifecycle Risk Overview

Widget:

- asset dengan `replacement_recommendation` tinggi
- asset dengan `risk_score` tinggi
- asset dengan `remaining_useful_life_months` terendah
- asset mendekati `expected_replacement_date`

Sumber data:

- `GET /api/v1/assets`
- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`

Kategori:

- `frontend-derived`

### 7.2 Asset Maintenance History Snapshot

Widget:

- total work order per asset
- downtime count
- failure count
- labor log count
- event count

Sumber data:

- `GET /api/v1/assets/{asset_id}/maintenance-history`

Kategori:

- `langsung jadi`

### 7.3 Component Replacement Watchlist

Widget:

- asset dengan histori replace komponen terbanyak
- komponen yang sering diganti
- asset dengan warning komponen pengganti

Sumber data:

- `GET /api/v1/assets/{asset_id}/component-history`
- `GET /api/v1/assets/{asset_id}/components`

Kategori:

- `frontend-derived`

## 8. Tracking & Verification Dashboard

### 8.1 Verification Health

Widget:

- total unverified asset
- top lokasi dengan unverified asset terbanyak
- aging bucket verifikasi:
  `>30 hari`, `>60 hari`, `>90 hari`

Sumber data:

- `GET /api/v1/reports/unverified-assets`

Kategori:

- `langsung jadi` untuk list
- `frontend-derived` untuk bucket dan grouping

### 8.2 Stocktake Discrepancy Board

Widget:

- total mismatch lokasi
- total missing asset
- unresolved discrepancy count
- hasil stocktake per session

Sumber data:

- `GET /api/v1/reports/location-discrepancies`
- `GET /api/v1/reports/missing-assets`
- `GET /api/v1/stocktakes`

Kategori:

- `frontend-derived`

### 8.3 Movement & Traceability Snapshot

Widget:

- scan event terbaru
- asset terakhir berpindah
- transfer yang belum selesai

Sumber data:

- `GET /api/v1/assets/{asset_id}/tracking`
- `GET /api/v1/asset-transfers`

Kategori:

- `frontend-derived`

## 9. Report Pages yang Disarankan

Selain dashboard, frontend sebaiknya punya halaman report khusus:

1. `Maintenance Backlog Report`
2. `Maintenance Cost Report`
3. `Maintenance SLA Report`
4. `Maintenance Reliability Report`
5. `Failure Analysis Report`
6. `Entitlement Expiry Report`
7. `Stocktake Discrepancy Report`
8. `Unverified Asset Report`
9. `Asset Lifecycle Risk Report`
10. `Schedule Stability Report`

## 10. Quick Wins Tanpa Backend Tambahan

Report berikut bisa sangat memperkaya UI tanpa perlu endpoint baru:

### 10.1 Schedule Stability Report

Bangun dari:

- `GET /api/v1/maintenance/schedules`
- `GET /api/v1/maintenance/schedules/{schedule_id}/events`

Isi:

- jumlah reschedule
- alasan reschedule
- aging schedule
- dominant schedule source

### 10.2 Maintenance Mix Report

Bangun dari:

- `GET /api/v1/maintenance/work-orders`
- `GET /api/v1/maintenance/requests`

Isi:

- preventive vs corrective vs breakdown vs predictive mix
- proporsi internal vs vendor
- proporsi request dengan warranty/contract entitlement

### 10.3 Asset Attention List

Bangun dari:

- `GET /api/v1/assets`
- `GET /api/v1/reports/unverified-assets`
- `GET /api/v1/maintenance/entitlements/expiring`

Isi:

- asset status abnormal
- asset belum diverifikasi
- asset dengan entitlement mendekati expiry

## 11. Kandidat Report Backend Berikutnya

Kalau nanti dashboard mulai berat di frontend, report berikut paling layak
dipindah menjadi endpoint backend khusus:

1. cost by asset aggregate
2. request-to-work-order funnel
3. schedule stability aggregate
4. lifecycle risk summary
5. maintenance mix by type/execution mode
6. vendor scorecard
7. first-time fix rate
8. replacement recommendation summary

## 12. Prioritas Implementasi Frontend

Urutan report yang paling bernilai:

### Tier 1

- backlog dashboard
- SLA dashboard
- cost dashboard
- reliability dashboard
- stocktake discrepancy dashboard

### Tier 2

- entitlement expiry cockpit
- schedule stability report
- lifecycle risk dashboard
- maintenance mix dashboard

### Tier 3

- predictive/condition trigger monitoring
- component replacement watchlist
- executive cross-domain dashboard
