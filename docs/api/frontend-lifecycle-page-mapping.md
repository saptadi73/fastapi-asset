# Frontend Lifecycle Page Mapping

Dokumen ini menjelaskan secara khusus bagaimana halaman `Lifecycle` di frontend
sebaiknya dibangun berdasarkan kemampuan backend yang tersedia pada
**Tuesday, July 28, 2026**.

Tujuan:

- menandai data lifecycle yang sudah benar-benar ada di backend
- menandai data yang masih bisa diturunkan dari field yang ada
- menandai area yang belum tersedia dan sebaiknya diberi label `coming soon`

Referensi:

- `docs/api/frontend-functional-blueprint.md`
- `docs/api/frontend-api-reference.md`
- `docs/implementation-gap-checklist.md`

## 1. Kesimpulan Singkat

Untuk domain lifecycle, backend saat ini **sudah siap** untuk:

- kondisi asset
- useful life dasar dari asset class
- target replacement planning di master asset
- lifecycle review
- risk score
- remaining life
- replacement recommendation
- retirement request
- approve retirement
- confirm retirement

Backend saat ini **belum lengkap** untuk:

- depreciation area
- depreciation method
- depreciation parameter
- depreciation snapshot / period balance
- nilai buku akuntansi / net book value
- perhitungan depresiasi finance-grade

Artinya:

- halaman `Lifecycle Operasional` bisa dibangun sekarang
- halaman `Lifecycle Finance` belum sebaiknya dianggap final

## 2. Struktur Halaman Lifecycle yang Disarankan

Route yang disarankan:

- `/assets/:assetId/lifecycle`

Tab atau section:

1. `Overview`
2. `Reviews`
3. `Replacement Planning`
4. `Retirement`
5. `Finance Lifecycle` (`coming soon`)

## 3. Lifecycle Overview

Bagian ini sebaiknya memakai data dari `GET /api/v1/assets/{asset_id}`.

### 3.1 Data yang sudah siap dari backend

- `condition_status`
- `replacement_strategy`
- `replacement_priority`
- `expected_replacement_date`
- `estimated_replacement_cost`
- `replacement_budget_year`
- `support_end_date`
- `vendor_end_of_sale_date`
- `vendor_end_of_support_date`
- `next_review_date`
- `retirement_date`

### 3.2 Data yang bisa diturunkan ringan

- `default_useful_life_months`
  sumber: `asset_class.default_useful_life_months`
- `planned useful life end`
  turunan dari:
  - `in_service_date`
  - `default_useful_life_months`

### 3.3 UI yang disarankan

Komponen:

- `LifecycleSummaryCard`
- `SupportDeadlineCard`
- `ReplacementPlanningCard`

Badge yang layak:

- `Condition`
- `Replacement Priority`
- `Support Ending Soon`
- `Review Due`

## 4. Lifecycle Reviews

Bagian ini memakai:

- `GET /api/v1/assets/{asset_id}/lifecycle-reviews`
- `POST /api/v1/assets/{asset_id}/lifecycle-reviews`

### 4.1 Data yang sudah siap

- `review_date`
- `condition_score`
- `remaining_life_months`
- `risk_score`
- `replacement_recommendation`
- `estimated_replacement_cost`
- `review_notes`
- `reviewed_by`
- `approved_by`

### 4.2 UI yang disarankan

Komponen:

- `LifecycleReviewTimeline`
- `RiskScoreTrend`
- `RemainingLifeTrend`
- `ReplacementRecommendationHistory`

### 4.3 Form create review

Field utama:

- `review_date`
- `condition_score`
- `replacement_recommendation`

Field opsional:

- `remaining_life_months`
- `risk_score`
- `estimated_replacement_cost`
- `review_notes`

Field yang tidak perlu ditonjolkan:

- `approved_by`

Alasan:

- lebih cocok diisi lewat workflow approval admin/supervisor, bukan form dasar

## 5. Replacement Planning

Ini adalah gabungan data master asset + latest lifecycle review.

### 5.1 Data yang bisa ditampilkan sekarang

Dari asset master:

- `expected_replacement_date`
- `replacement_strategy`
- `replacement_priority`
- `estimated_replacement_cost`
- `replacement_budget_year`
- `support_end_date`
- `vendor_end_of_sale_date`
- `vendor_end_of_support_date`

Dari lifecycle review terbaru:

- `remaining_life_months`
- `risk_score`
- `replacement_recommendation`

### 5.2 Data yang masih derived

Frontend bisa turunkan:

- `days until replacement target`
- `support expiry proximity`
- `budget year label`
- `replacement urgency`

Contoh rule UI:

- jika `risk_score >= 80`, tandai `urgent`
- jika `remaining_life_months <= 6`, tandai `near end-of-life`
- jika `expected_replacement_date` dalam 90 hari, tampilkan alert

### 5.3 Yang belum tersedia

Belum ada endpoint backend khusus untuk:

- consolidated replacement pipeline
- aggregated replacement portfolio
- replacement optimization ranking lintas asset

Jadi untuk sekarang:

- tampilkan replacement planning per asset
- jangan mengklaim ada ranking portfolio enterprise yang dihitung backend

## 6. Retirement

Bagian ini memakai:

- `GET /api/v1/assets/{asset_id}/retirement-requests`
- `GET /api/v1/retirement-requests/{retirement_id}`
- `POST /api/v1/assets/{asset_id}/retirement-requests`
- `POST /api/v1/retirement-requests/{retirement_id}/approve`
- `POST /api/v1/retirement-requests/{retirement_id}/confirm`

### 6.1 Data yang sudah siap

- `retirement_number`
- `retirement_type`
- `request_date`
- `effective_date`
- `status`
- `proceeds_amount`
- `buyer_partner_id`
- `reason`
- `approved_by`
- `sap_retirement_doc_entry`
- `sap_trans_id`

### 6.2 UI yang disarankan

Komponen:

- `RetirementStatusCard`
- `RetirementRequestTimeline`
- `RetirementFinanceSnippet`

Action:

- `Create Retirement Request`
- `Approve`
- `Confirm`

### 6.3 Catatan penting

Backend retirement yang ada sekarang sudah operasional untuk workflow:

- request
- approval
- confirmation
- update final asset status

Jadi bagian `Retirement` **bukan placeholder**, sudah bisa dipakai serius.

## 7. Useful Life

### 7.1 Yang sudah ada

- `default_useful_life_months` di `asset class`
- `remaining_life_months` di lifecycle review

### 7.2 Yang belum ada

Belum ada perhitungan backend standar seperti:

- `book useful life consumed %`
- `depreciation life consumed %`
- `remaining useful life otomatis hasil engine`

### 7.3 Rekomendasi UI

Tampilkan dua lapis:

- `Class Useful Life`: dari asset class
- `Latest Reviewed Remaining Life`: dari lifecycle review terbaru

Jangan menyebut ini sebagai:

- `financial useful life`
- `depreciation useful life`

kecuali nanti domain depreciation sudah selesai.

## 8. Nilai / Value

### 8.1 Yang tersedia sekarang

Masih terbatas pada:

- `estimated_replacement_cost`
- `proceeds_amount` retirement

### 8.2 Yang belum tersedia

Belum ada backend lifecycle value penuh seperti:

- acquisition cost normalized lifecycle view
- accumulated depreciation
- net book value
- carrying amount per period
- impairment / salvage accounting view

### 8.3 Konsekuensi UI

Di halaman Lifecycle saat ini, label yang aman:

- `Estimated Replacement Cost`
- `Retirement Proceeds`

Label yang **jangan dulu** dipakai seolah final:

- `Book Value`
- `Current Asset Value`
- `Depreciated Value`
- `Accumulated Depreciation`

Kecuali nanti backend depreciation sudah selesai.

## 9. Finance Lifecycle

Status saat ini:

- `coming soon`

Alasan:

- gap `D4 Depreciation Domain` belum selesai
- belum ada perhitungan atau snapshot finance lifecycle yang stabil

Isi placeholder yang disarankan:

- depreciation area
- depreciation method
- useful life finance
- accumulated depreciation
- net book value
- period movement

## 10. Mapping Siap Pakai vs Belum

### Siap dipakai sekarang

- condition
- class useful life
- expected replacement date
- support end / end-of-sale / end-of-support
- replacement strategy
- replacement priority
- replacement cost estimate
- next review date
- lifecycle review history
- risk score
- remaining life
- replacement recommendation
- retirement workflow

### Bisa diturunkan ringan di frontend

- planned end-of-life date
- support countdown
- replacement urgency badge
- review overdue badge
- latest lifecycle summary card

### Belum ada / jangan dianggap final

- depreciation
- net book value
- accumulated depreciation
- finance lifecycle snapshots
- accounting value trend

## 11. Rekomendasi Tampilan

Kalau ingin halaman lifecycle terasa kaya tetapi jujur terhadap backend,
susun seperti ini:

### Hero summary

- condition
- latest risk score
- latest remaining life
- replacement recommendation

### Replacement planning block

- expected replacement date
- support deadlines
- replacement strategy
- estimated replacement cost

### Review history block

- timeline review
- trend condition score
- trend risk score

### Retirement block

- active retirement request
- status
- confirm history

### Finance block

- tampilkan `coming soon`

## 12. Saran Label UX

Supaya tidak misleading, gunakan label:

- `Latest Reviewed Remaining Life`
- `Estimated Replacement Cost`
- `Lifecycle Risk Score`
- `Replacement Recommendation`
- `Support Deadline`

Hindari label yang terlalu finance-heavy jika datanya belum ada:

- `Book Value`
- `Residual Value`
- `Depreciation Value`
- `Financial Asset Value`
