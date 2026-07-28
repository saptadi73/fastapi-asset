# Frontend Functional Blueprint

Dokumen ini merangkum kebutuhan fungsional frontend berdasarkan kemampuan
backend yang sudah tersedia dan tervalidasi live pada **Tuesday, July 28, 2026**.

Tujuan dokumen ini:

- memberi gambaran menu utama aplikasi;
- menjelaskan halaman demi halaman yang perlu ditampilkan;
- memetakan dashboard dan laporan yang selaras dengan endpoint backend;
- merekomendasikan workflow UI yang konsisten dengan business rule backend.

Dokumen ini tidak menggantikan kontrak API. Untuk kontrak field dan sample
response, gunakan juga:

- `docs/api/frontend-api-reference.md`
- `docs/api/frontend-seed-scenarios.md`
- `docs/api/frontend-page-endpoint-map.md`
- `artifacts/frontend_endpoint_samples.json`

## 1. Struktur Menu Utama

Rekomendasi menu sidebar/top-level:

1. Dashboard
2. Asset Registry
3. Asset Transfers
4. Leases
5. Software Licenses
6. Tracking & Stocktake
7. Maintenance
8. Reports
9. Master Data
10. Authentication / User Session

## 2. Dashboard

Tujuan:

- memberi ringkasan operasional cepat;
- menjadi landing page setelah login;
- menampilkan status pekerjaan yang perlu perhatian.

### 2.1 Dashboard Utama

Widget yang direkomendasikan:

- total asset aktif
- asset dengan status tidak normal
- transfer asset yang masih terbuka
- stocktake aktif atau belum disetujui
- maintenance request terbuka
- work order aktif
- ringkasan backlog maintenance
- daftar asset belum diverifikasi

Backend yang paling relevan saat ini:

- `GET /api/v1/assets`
- `GET /api/v1/asset-transfers`
- `GET /api/v1/stocktakes`
- `GET /api/v1/maintenance/requests`
- `GET /api/v1/maintenance/work-orders`
- `GET /api/v1/maintenance/reports/backlog`
- `GET /api/v1/reports/unverified-assets`

Catatan UI:

- gunakan card summary untuk angka utama;
- gunakan table ringkas untuk item yang butuh tindak lanjut;
- sediakan link drilldown ke halaman list terkait.

### 2.2 Dashboard Maintenance

Widget yang direkomendasikan:

- backlog maintenance
- compliance SLA
- trend reliability
- total downtime
- cost aktual maintenance
- failure analysis ringkas

Backend:

- `GET /api/v1/maintenance/reports/backlog`
- `GET /api/v1/maintenance/reports/sla`
- `GET /api/v1/maintenance/reports/reliability`
- `GET /api/v1/maintenance/reports/cost`
- `GET /api/v1/maintenance/reports/failure-analysis`

Rekomendasi visual:

- card KPI untuk summary;
- bar/line chart untuk trend;
- tabel top asset failure;
- tabel open request dan open work order.

## 3. Asset Registry

Tujuan:

- menjadi pusat data master asset operasional;
- menyediakan histori, tracking, dan maintenance context pada level asset.

### 3.1 Asset List

Fungsi halaman:

- menampilkan seluruh asset;
- filter berdasarkan category, class, location, status;
- pencarian asset code dan asset name;
- navigasi ke asset detail;
- entry point pembuatan asset baru.

Komponen UI:

- table asset
- quick filters
- search bar
- pagination
- tombol `Create Asset`

### 3.2 Asset Create / Edit

Fungsi halaman:

- membuat asset baru;
- memperbarui asset master;
- mengisi dynamic attributes berdasarkan category.

Komponen UI:

- form data utama asset
- section financial/reference
- section dynamic attributes
- validasi field wajib

Workflow yang direkomendasikan:

1. pilih category
2. muat attribute definitions
3. isi data utama asset
4. simpan asset
5. simpan attribute values

### 3.3 Asset Detail

Fungsi halaman:

- menampilkan detail lengkap asset;
- menjadi hub untuk history dan activity asset.

Tab yang direkomendasikan:

1. Overview
2. Attributes
3. Ownership
4. Assignment
5. Components
6. Lifecycle
7. Retirement
8. Status History
9. Location History
10. Timeline
11. Tracking
12. Maintenance History

Konten tab:

- `Overview`: data master asset, category, class, status, current location
- `Attributes`: daftar dynamic attribute
- `Ownership`: histori ownership
- `Assignment`: histori assignment dan PIC/custodian
- `Components`: komponen terpasang dan histori install/replace/remove
- `Lifecycle`: review score, risk score, remaining life, replacement recommendation
- `Retirement`: request retirement, approval status, SAP confirmation reference
- `Status History`: histori perubahan status dan condition
- `Location History`: histori perpindahan lokasi
- `Timeline`: timeline gabungan
- `Tracking`: event scan/tracking
- `Maintenance History`: histori work order dan maintenance asset

### 3.4 Asset Action Model

Aksi yang disarankan pada asset detail:

- edit asset
- record location change
- create assignment
- create ownership record
- install component
- replace component
- remove component
- create lifecycle review
- create retirement request
- approve retirement request
- confirm retirement request
- create status change
- view transfer history

Panel tambahan yang direkomendasikan pada asset detail:

- expected replacement date
- support end date
- vendor end-of-sale
- vendor end-of-support
- replacement strategy
- replacement priority
- estimated replacement cost
- next review date

Komponen UI yang direkomendasikan pada tab Components:

- current installed component table
- component history timeline
- action drawer install/remove/replace
- warning badge bila komponen pengganti belum terpasang

Catatan penting:

- perubahan workflow jangan dicampur dalam satu form `PATCH asset`;
- gunakan command endpoint yang sudah disediakan backend untuk histori yang
  perlu audit trail.

## 4. Asset Transfers

Tujuan:

- mengelola perpindahan asset antar lokasi atau organisasi;
- memberi visibility status transfer dari draft sampai selesai.

### 4.1 Transfer List

Fungsi halaman:

- menampilkan daftar transfer;
- filter by status dan lokasi tujuan;
- melihat transfer yang masih menunggu submit/approve/complete.

Kolom yang direkomendasikan:

- transfer number
- transfer date
- from location
- to location
- movement purpose
- status
- requested by
- approved at
- received at

### 4.2 Transfer Detail

Fungsi halaman:

- menampilkan header transfer;
- item asset yang dipindahkan;
- histori approval sederhana berbasis status field.

Aksi yang direkomendasikan:

- submit
- approve
- complete

Workflow backend yang direkomendasikan:

1. create transfer draft
2. review detail
3. submit
4. approve
5. complete

Frontend sebaiknya:

- disable action jika status tidak sesuai;
- menampilkan chip status yang jelas;
- menampilkan perubahan lokasi asset setelah complete.

## 5. Lease Management

Tujuan:

- memisahkan aset sewa dari ownership biasa;
- memberi visibilitas kontrak, item aset, dan payment lease;
- membantu frontend menampilkan kontrak aktif yang melekat pada aset.

### 5.1 Lease Contract List

Fungsi halaman:

- menampilkan daftar lease contract;
- filter berdasarkan status, lease type, dan lessor;
- membuka detail kontrak.

Kolom yang direkomendasikan:

- contract number
- lessor
- lease type
- start date
- end date
- billing frequency
- payment amount
- currency
- status

### 5.2 Lease Contract Detail

Tab yang direkomendasikan:

1. Overview
2. Lease Items
3. Payments

Konten utama:

- informasi lessor dan lessee
- accounting treatment
- periode kontrak
- opsi extension dan auto renewal
- daftar asset item beserta return condition
- daftar payment due, paid, atau overdue

Aksi yang direkomendasikan:

- create lease contract
- add lease item
- add payment

Catatan frontend:

- tampilkan warning bila kontrak aktif mendekati end date
- tampilkan badge asset leased pada asset detail bila asset muncul di lease item

## 6. Software License Management

Tujuan:

- mengelola entitlement software terpisah dari asset hardware;
- memantau kapasitas seat dan tanggal expiry;
- merekam assignment lisensi ke asset atau named user.

### 6.1 Software License List

Fungsi halaman:

- menampilkan seluruh software license;
- filter by status, product, expiry, dan capacity full;
- membuka detail lisensi.

Kolom yang direkomendasikan:

- product code
- product name
- license model
- license metric
- license quantity
- used quantity
- available quantity
- expiry date
- status
- expires soon badge
- capacity full badge

### 6.2 Software License Detail

Tab yang direkomendasikan:

1. Overview
2. Assignments

Konten utama:

- informasi product dan supplier
- tanggal start, expiry, support end, dan update entitlement end
- quantity summary
- daftar assignment aktif dan released

Aksi yang direkomendasikan:

- create software product
- create software license
- assign license
- release assignment

Catatan frontend:

- tampilkan warning expiry dengan basis tanggal operasional saat ini,
  yaitu Monday, July 27, 2026 pada seed sample
- pada assignment form, tampilkan sisa seat sebelum submit

## 7. Tracking & Stocktake

Tujuan:

- menangani visibilitas scan asset dan proses verifikasi fisik stocktake.

### 5.1 Tracking Timeline

Fungsi halaman:

- melihat riwayat scan asset;
- menampilkan lokasi/event terakhir.

Komponen UI:

- timeline event scan
- filter berdasarkan source atau tanggal
- informasi user/petugas scan

### 5.2 Stocktake List

Fungsi halaman:

- menampilkan sesi stocktake;
- memisahkan status planned, in progress, completed, approved.

Kolom yang direkomendasikan:

- stocktake number
- stocktake date
- target location
- status
- started at
- completed at
- approved at

### 5.3 Stocktake Detail

Fungsi halaman:

- menampilkan metadata sesi;
- expected vs scanned assets;
- discrepancy outcome;
- aksi workflow stocktake.

Tab yang direkomendasikan:

1. Overview
2. Scanned Items
3. Discrepancies
4. Audit Trail

Aksi yang direkomendasikan:

- start
- scan
- complete
- approve

Workflow backend yang direkomendasikan:

1. create stocktake
2. start session
3. lakukan scan
4. complete session
5. approve result

## 6. Maintenance

Tujuan:

- menjadi area operasional maintenance end-to-end, dari request sampai close.

### 6.1 Maintenance Navigation

Submenu yang direkomendasikan:

1. Dashboard
2. Requests
3. Work Orders
4. Schedules
5. Plans
6. Failures & Findings
7. Teams
8. Contract & Warranty
9. Checklist Templates
10. Master Codes

### 6.2 Maintenance Requests

#### Request List

Fungsi halaman:

- inbox permintaan maintenance;
- filter status, priority, asset, vendor, date;
- entry point create request baru.

Kolom yang direkomendasikan:

- request number
- reported at
- asset
- title
- priority
- status
- requested vendor
- required response at

#### Request Detail

Tab yang direkomendasikan:

1. Overview
2. Attachments
3. Work Order Links
4. Audit / Status

Aksi yang direkomendasikan:

- create batch request multi-asset
- submit
- triage
- approve
- reject
- convert to work order
- add attachment
- view attachment version history
- upload attachment new version
- view attachment audit trail
- resolve secure download link

Workflow backend yang direkomendasikan:

1. create request
2. submit
3. triage
4. approve atau reject
5. jika approved, convert ke work order

Frontend sebaiknya:

- mengunci action berdasarkan status;
- menonjolkan target SLA response dan resolution;
- menampilkan hubungan request ke asset dan work order;
- pada tab attachment, tampilkan versi aktif, histori versi, dan audit trail file.
- gunakan flow aman `GET attachment download -> GET secure download URL`
  saat user menekan tombol download.
- jika contract dan warranty sama-sama aktif tetapi vendor entitlement berbeda,
  paksa user memilih vendor eksplisit saat triage.
- untuk skenario gangguan massal atau inspeksi gabungan, sediakan mode batch
  request yang membuat beberapa request asset-spesifik dalam satu submit.

Panel tambahan yang direkomendasikan pada request detail:

- contract aktif
- warranty aktif
- histori warranty claim
- warning expiry warranty/contract bila mendekati tanggal akhir
- vendor hasil coverage
- sumber vendor entitlement: `MANUAL`, `CONTRACT`, atau `WARRANTY`
- rekomendasi execution mode dari histori SLA snapshot
- target SLA response
- target SLA resolution
- histori SLA snapshot
- indikator escalation response

### 6.3 Maintenance Work Orders

#### Work Order List

Fungsi halaman:

- daftar eksekusi pekerjaan maintenance;
- filter status, maintenance type, asset, team, vendor.

Kolom yang direkomendasikan:

- work order number
- asset
- maintenance type
- priority
- status
- team
- planned start
- planned end
- actual end

#### Work Order Detail

Ini adalah salah satu halaman paling penting di frontend.

Tab yang direkomendasikan:

1. Overview
2. Attachments
3. Assignments
4. Required Skills
5. Material Planning
6. Vendor Personnel
7. Parts
8. Labor Logs
9. Downtimes
10. Failures
11. Checklist
12. Events

Konten utama:

- header WO dan status chip
- relasi ke request/plan bila ada
- info asset
- info vendor/team
- daftar required skill dan status pemenuhan skill assignee
- perbandingan planned part, reserved part, issued part, dan returned part
- daftar teknisi vendor beserta check-in/check-out
- biaya aktual dan estimasi
- actual start/end

Aksi yang direkomendasikan:

- approve
- assign
- add required skill
- start
- add part requirement
- add vendor personnel
- hold
- resume
- add part usage
- add labor log
- add downtime
- add failure
- start checklist
- complete
- verify
- close
- cancel
- add attachment
- review attachment history
- resolve secure download link

Workflow backend yang direkomendasikan:

1. create atau convert dari request
2. approve
3. tetapkan required skill bila dibutuhkan
4. assign
5. start
6. input operational data selama pekerjaan berjalan
7. complete
8. verify bila diperlukan
9. close

Frontend sebaiknya:

- memunculkan tombol aksi hanya pada status valid;
- menampilkan warning skill mismatch sebelum assign disubmit;
- memisahkan data transaksi per tab;
- menyediakan panel cost summary dan event timeline;
- pada tab attachment, sediakan version history, upload revisi file, dan audit trail.
- untuk tombol download, frontend sebaiknya terlebih dahulu meminta secure
  download link yang berumur pendek.
- sebelum submit `complete`, tampilkan hasil rollup `actual_part_cost` dan
  `actual_labor_cost` dari transaksi yang sudah diinput agar payload frontend
  tidak mismatch dengan validasi backend.
- untuk work order `BREAKDOWN`, tampilkan gate bahwa failure dan RCA wajib
  selesai sebelum `complete` dan `close`.
- untuk work order `PREVENTIVE`, `INSPECTION`, `CALIBRATION`, atau work order
  berbasis plan, tampilkan gate bahwa checklist completed wajib ada.
- sembunyikan aksi `cancel` bila work order sudah pernah start atau sudah punya
  jejak eksekusi seperti part usage, labor log, failure, atau checklist.
- setelah work order masuk `COMPLETED` atau `VERIFICATION`, kunci form part
  usage, labor log, dan create failure agar status akhir tetap final.

Jika work order berasal dari request yang sudah ditriage, frontend sebaiknya
menampilkan badge entitlement untuk contract atau warranty yang sedang melekat,
beserta sumber vendor entitlement dan rekomendasi mode eksekusi yang tersimpan
di SLA snapshot terakhir.

### 6.4 Maintenance Schedules

#### Schedule List

Fungsi halaman:

- menampilkan due schedule dari plan atau request/work order;
- filter planned, confirmed, postponed, completed.

Kolom yang direkomendasikan:

- schedule number
- source
- asset
- planned start
- planned end
- team/vendor
- status

#### Schedule Detail

Aksi yang direkomendasikan:

- confirm
- reschedule

Workflow backend yang direkomendasikan:

1. schedule dihasilkan dari plan atau dibuat manual
2. confirm
3. bila perlu, reschedule

### 6.5 Maintenance Plans

#### Plan List

Fungsi halaman:

- daftar preventive plans;
- filter maintenance type, active flag, asset scope.

Kolom yang direkomendasikan:

- plan code
- plan name
- maintenance type
- scope asset/category
- default priority
- default team
- next due date
- active status

#### Plan Detail

Tab yang direkomendasikan:

1. Overview
2. Assets
3. Generation History / Schedule Result

Aksi yang direkomendasikan:

- add plan asset
- generate schedules

Workflow backend yang direkomendasikan:

1. create plan
2. tambahkan target asset bila perlu
3. generate schedule
4. monitor hasil schedule

### 6.6 Failures & Findings

#### Failure List

Fungsi halaman:

- daftar failure;
- filter by asset, work order, status, failure mode, root cause.

Kolom yang direkomendasikan:

- failure number
- detected at
- asset
- work order
- severity
- status
- caused shutdown
- downtime minutes

#### Failure Detail

Tab yang direkomendasikan:

1. Overview
2. RCA
3. Attachments

Aksi yang direkomendasikan:

- update failure
- complete RCA fields
- add attachment

Catatan UI:

- bila failure berasal dari work order `BREAKDOWN`, status RCA perlu dibuat
  sangat menonjol karena menjadi prasyarat penyelesaian work order.

#### Finding Detail

Fungsi halaman:

- menampilkan abnormal finding dari checklist;
- membuat follow-up request bila dibutuhkan.

Aksi yang direkomendasikan:

- add attachment
- create follow-up request

### 6.7 Teams

Fungsi halaman:

- mengelola team maintenance internal;
- melihat anggota team dan default location.

Halaman yang direkomendasikan:

- Team List
- Team Detail

Action:

- create team
- add member

### 6.8 Checklist Templates

Fungsi halaman:

- mengelola template checklist untuk preventive atau inspection work.

Halaman yang direkomendasikan:

- Template List
- Template Detail

Action:

- create template
- review items

### 6.9 Master Codes

Fungsi halaman:

- mengelola priority, symptom codes, failure modes, root cause codes.

Submenu yang direkomendasikan:

1. Priorities
2. Symptom Codes
3. Failure Modes
4. Root Cause Codes

## 7. Reports

Tujuan:

- memisahkan area reporting dari transaksi harian;
- menyediakan halaman yang fokus ke analitik dan monitoring.

Rekomendasi submenu Reports:

1. Asset Verification
2. Asset Discrepancies
3. Maintenance Backlog
4. Maintenance Cost
5. Maintenance SLA
6. Maintenance Reliability
7. Failure Analysis

### 7.1 Asset Verification Report

Halaman yang direkomendasikan:

- Unverified Assets

Backend:

- `GET /api/v1/reports/unverified-assets`

Kolom:

- asset code
- asset name
- last verified at
- days since verified
- current location

### 7.2 Asset Discrepancy Reports

Halaman yang direkomendasikan:

- Location Discrepancies
- Missing Assets

Backend:

- `GET /api/v1/reports/location-discrepancies`
- `GET /api/v1/reports/missing-assets`

### 7.3 Maintenance Backlog Report

Backend:

- `GET /api/v1/maintenance/reports/backlog`

UI yang direkomendasikan:

- KPI cards
- aging buckets
- open request dan open work order summaries

### 7.4 Maintenance Cost Report

Backend:

- `GET /api/v1/maintenance/reports/cost`

UI yang direkomendasikan:

- table cost per work order
- filter asset dan date range
- summary total labor, part, vendor cost

### 7.5 Maintenance SLA Report

Backend:

- `GET /api/v1/maintenance/reports/sla`

UI yang direkomendasikan:

- SLA compliance cards
- response vs resolution compliance
- breached items summary

### 7.6 Maintenance Reliability Report

Backend:

- `GET /api/v1/maintenance/reports/reliability`

UI yang direkomendasikan:

- MTBF
- downtime total
- planned vs unplanned ratio
- repeat failure summary

### 7.7 Failure Analysis Report

Backend:

- `GET /api/v1/maintenance/reports/failure-analysis`

UI yang direkomendasikan:

- top asset by failure count
- root cause buckets
- failure mode buckets
- RCA completion rate
- repeat failure rate

## 8. Master Data

Tujuan:

- memisahkan konfigurasi dari transaksi.

Rekomendasi submenu:

1. Business Partners
2. Asset Categories
3. Asset Classes
4. Asset Locations
5. Asset Attribute Definitions
6. Maintenance Priorities
7. Maintenance Teams
8. Checklist Templates
9. Symptom Codes
10. Failure Modes
11. Root Cause Codes

## 9. Workflow yang Direkomendasikan dari Sisi Backend

### 9.1 Asset Lifecycle UI

Alur utama:

1. buat master asset
2. isi attribute
3. catat ownership
4. catat assignment
5. catat status change bila ada perubahan kondisi
6. catat location change atau transfer bila berpindah
7. lihat tracking dan maintenance history pada asset detail

### 9.2 Transfer Workflow UI

Alur utama:

1. create draft transfer
2. review item asset
3. submit
4. approve
5. complete

### 9.3 Stocktake Workflow UI

Alur utama:

1. create stocktake
2. start
3. lakukan scan
4. review discrepancies
5. complete
6. approve

### 9.4 Corrective Maintenance Workflow UI

Alur utama:

1. create request
2. submit request
3. triage
4. approve
5. convert to work order
6. approve work order
7. assign technician/team
8. start work
9. input parts/labor/downtime/failure
10. complete
11. verify
12. close

### 9.5 Preventive Maintenance Workflow UI

Alur utama:

1. create maintenance plan
2. assign target assets
3. generate schedules berdasarkan trigger calendar, meter, condition, atau predictive
4. review due context, schedule source, lalu confirm atau reschedule schedules
5. create atau link work orders sesuai kebutuhan operasional
6. eksekusi work order
7. tutup dan review maintenance history

Kebutuhan layar yang sekarang masuk akal:

- planner perlu form generate yang bisa menampilkan input `meter_reading_value`
  bila trigger plan berbasis meter
- planner perlu panel `condition_snapshot` bila trigger plan berbasis condition
- planner perlu panel `predictive_snapshot` bila trigger plan berbasis predictive
- detail schedule perlu tab `event history` untuk melihat `CREATED`,
  `GENERATED`, `CONFIRMED`, dan `RESCHEDULED`

### 9.6 Checklist-to-Finding-to-Request Workflow

Alur utama:

1. start checklist execution
2. submit checklist result
3. backend membuat finding abnormal otomatis bila hasil tidak normal
4. user review finding
5. create follow-up request dari finding bila perlu

Ini penting untuk frontend karena:

- finding tidak selalu dibuat manual;
- finding bisa muncul sebagai output dari checklist result;
- request bisa menjadi turunan dari finding dan perlu ditampilkan traceability-nya.

## 10. Prioritas Implementasi Frontend

Urutan yang paling masuk akal:

### Phase 1

- login dan auth state
- asset list
- asset detail
- business partner master ringan
- asset transfer list/detail

### Phase 2

- tracking timeline
- stocktake list/detail
- dashboard asset verification/discrepancy

### Phase 3

- maintenance request list/detail
- maintenance work order list/detail
- maintenance dashboard

### Phase 4

- maintenance plans
- maintenance schedules
- failures, findings, checklist
- maintenance reporting lengkap

## 11. Prinsip UX yang Direkomendasikan

- gunakan status chip yang konsisten di seluruh modul workflow;
- tampilkan action button hanya bila status backend mengizinkan;
- pisahkan data transaksi ke dalam tab agar halaman detail tidak terlalu padat;
- gunakan drawer/modal hanya untuk aksi kecil, bukan untuk seluruh halaman detail;
- tampilkan audit info penting seperti `reported_at`, `approved_at`, `started_at`,
  `completed_at`, dan `closed_at`;
- tampilkan relasi antar entitas secara eksplisit, misalnya request ke work order,
  work order ke asset, checklist ke finding, finding ke follow-up request.
