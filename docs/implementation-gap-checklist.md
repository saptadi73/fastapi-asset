# Implementation Gap Checklist

Dokumen ini merangkum gap antara implementasi backend saat ini dan target yang
dijelaskan di `asset_management_sap_b1_fastapi_technical_baseline.md`.

Tanggal acuan review: **Tuesday, July 28, 2026**.

Tujuan dokumen ini:

- memisahkan feature yang sudah ada vs yang belum;
- membagi backlog menjadi tahap implementasi yang realistis;
- membantu prioritisasi engineering setelah MVP operasional saat ini.

## Ringkasan Status Saat Ini

Backend yang sudah aktif dan tervalidasi live:

- authentication dasar dengan JWT
- business partners
- asset registry operasional
- asset transfer
- asset lifecycle review dan retirement workflow dasar
- attachments dasar
- tracking scan
- stocktake
- maintenance corrective dasar
- maintenance preventive dasar
- maintenance checklist, finding, failure, dan reporting inti
- lease contracts
- software licenses

Gap utama yang masih terlihat:

- domain contract dan entitlement belum dibangun penuh
- domain depreciation dan SAP integration belum tersedia
- beberapa business rule baseline lanjutan belum diterapkan

## A. Sudah Tersedia

Checklist ini menandai area yang secara umum sudah ada di backend saat ini.

### A1. Core Asset Operations

- [x] asset category
- [x] asset class
- [x] asset location
- [x] asset registry create/list/detail/update
- [x] asset attribute definition
- [x] asset attribute value
- [x] asset ownership
- [x] asset assignment create
- [x] asset status change
- [x] asset location history
- [x] asset assignment history
- [x] asset status history
- [x] asset timeline

### A2. Movement and Verification

- [x] asset transfer create
- [x] transfer submit
- [x] transfer approve
- [x] transfer complete
- [x] tracking scan event
- [x] stocktake create
- [x] stocktake start
- [x] stocktake scan
- [x] stocktake complete
- [x] stocktake approve

### A3. Maintenance Foundations

- [x] maintenance priority
- [x] maintenance request create/list/detail
- [x] maintenance request submit
- [x] maintenance request triage
- [x] maintenance request approve
- [x] maintenance request reject
- [x] convert request to work order
- [x] maintenance team
- [x] maintenance team member
- [x] maintenance schedule create/list/detail
- [x] maintenance schedule confirm
- [x] maintenance schedule reschedule
- [x] maintenance plan create/list/detail
- [x] maintenance plan asset
- [x] generate schedule from plan
- [x] work order create/list/detail
- [x] work order approve
- [x] work order assign
- [x] work order start
- [x] work order complete
- [x] work order verify
- [x] work order close
- [x] work order events
- [x] work order part usage
- [x] work order labor log
- [x] work order downtime

### A4. Reliability and Findings Basics

- [x] symptom codes
- [x] failure modes
- [x] root cause codes
- [x] failure create/list/detail/update
- [x] checklist template
- [x] checklist execution start
- [x] checklist result submit
- [x] finding auto-create from abnormal checklist result
- [x] follow-up request from finding
- [x] asset maintenance history
- [x] maintenance backlog report
- [x] maintenance cost report
- [x] maintenance SLA report
- [x] maintenance reliability report
- [x] maintenance failure analysis report

## B. Gap Prioritas MVP+

Ini adalah gap yang menurut saya paling penting untuk dikerjakan segera setelah
fondasi saat ini stabil, karena efeknya langsung ke workflow operasional.

### B1. Contract/Warranty/SLA Validation

Status:

- [x] validasi coverage maintenance contract saat triage request
- [x] validasi coverage warranty saat triage request
- [x] validasi coverage saat convert request ke work order
- [x] snapshot SLA per request
- [x] aturan escalation SLA

Alasan prioritas:

- baseline menekankan request tidak boleh langsung dianggap siap kerja tanpa
  resolusi entitlement;
- ini memengaruhi keputusan vendor/internal, biaya, dan auditability.

Dependency:

- master maintenance contract
- master warranty
- relasi asset ke contract/warranty

### B2. Work Order Lifecycle Commands Tambahan

Status:

- [x] hold work order
- [x] resume work order
- [x] cancel work order

Alasan prioritas:

- status machine work order di lapangan biasanya tidak cukup hanya
  `APPROVED -> ASSIGNED -> IN_PROGRESS -> COMPLETED -> VERIFIED -> CLOSED`;
- tanpa hold/resume/cancel, UI dan operasi lapangan akan cepat mentok.

### B3. Asset Assignment Return

Status:

- [x] return assignment by assignment id

Alasan prioritas:

- baseline menyebut command `POST /assignments/{assignment_id}/return`;
- saat ini assignment baru bisa dibuat, tetapi skenario pengembalian eksplisit
  belum ada.

### B4. Attachment Capability Lanjutan

Status:

- [x] download attachment/file
- [x] version history file
- [x] replace/upload new version
- [x] audit trail eksplisit untuk file lifecycle

Alasan prioritas:

- backend sekarang sudah punya versioning, secure download link, dan immutable
  file event trail;
- frontend dokumen dan evidentiary workflow akan butuh ini.

## C. Phase 2 Backlog

Tahap ini cocok setelah backlog prioritas MVP+ mulai tertutup.

### C1. Warranty Domain

Status:

- [x] asset warranties
- [x] warranty claims
- [x] expiry monitoring

Manfaat:

- memperkuat keputusan apakah request harus ditangani vendor/manufacturer;
- mendukung traceability biaya dan claim.

### C2. Maintenance Contracts

Status:

- [x] maintenance contracts
- [x] maintenance contract assets
- [x] coverage start/end
- [x] preventive/corrective inclusion flags

Manfaat:

- menjadi dasar validasi entitlement;
- menjadi dasar vendor SLA dashboard.

### C3. Vendor Personnel

Status:

- [x] maintenance vendor personnel

Manfaat:

- penting untuk work order eksternal;
- memisahkan teknisi vendor dari anggota tim internal.

### C4. Spare Part Requirements

Status:

- [x] maintenance part requirements
- [x] part planning before actual usage

Manfaat:

- memisahkan kebutuhan part yang direncanakan vs yang benar-benar dipakai;
- membantu material readiness dan future SAP integration.

### C5. Skills and Capability Matching

Status:

- [x] maintenance skills
- [x] employee maintenance skills
- [x] validasi skill terhadap assignment

Manfaat:

- memastikan assignment tidak hanya berdasarkan user/team, tetapi kapabilitas.

## D. Phase 3 Backlog

Tahap ini mulai masuk ke domain yang lebih luas dari asset management baseline.

### D1. Lease Domain

Status:

- [x] lease contracts
- [x] lease contract assets/items
- [x] lease payments
- [x] active lease overlap rules

### D2. Software License Domain

Status:

- [x] software licenses
- [x] software license assignments
- [x] release software license assignment
- [x] capacity and expiry monitoring

### D3. Asset Lifecycle Review and Retirement

Status:

- [x] lifecycle reviews
- [x] retirement requests
- [x] disposal/retirement workflow foundation

Manfaat:

- penting untuk sisi lifecycle penuh dan koneksi ke proses finansial SAP B1.

### D4. Depreciation Domain

Status:

- [ ] depreciation areas
- [ ] depreciation methods
- [ ] asset depreciation parameters
- [ ] depreciation snapshots/period balances

Catatan:

- ini bukan prioritas operasional maintenance, tetapi penting untuk baseline
  lengkap dan integrasi sisi finance/SAP.

## E. Phase 4 Backlog

Tahap ini fokus pada integrasi, optimization, dan analytical maturity.

### E1. SAP Integration Domain

Status:

- [ ] SAP integration mappings
- [ ] reconciliation API
- [ ] integration error log
- [ ] retry integration error
- [ ] goods issue/return integration for maintenance parts
- [ ] purchase request integration

### E2. Predictive and Condition-Based Maintenance

Status:

- [x] predictive trigger
- [x] condition-based trigger
- [x] sensor/meter driven due generation beyond current simple foundation

### E3. Advanced Reliability and Optimization

Status:

- [ ] first-time fix rate
- [ ] vendor scorecard
- [ ] checklist finding closure rate
- [ ] replacement recommendation
- [ ] maintenance cost vs replacement value

## F. Logic and Service Review Checklist

Selain feature besar, berikut logic/service baseline yang perlu ditinjau lagi.

### F1. Maintenance Request Logic

- [x] cek coverage contract/warranty saat triage
- [x] cek pilihan internal vs vendor berdasarkan entitlement
- [x] cek SLA mapping otomatis dari priority/contract
- [x] dukung multi-asset request bila memang tetap dibutuhkan

### F2. Work Order Logic

- [x] state machine lengkap termasuk hold/resume/cancel
- [x] cost rollup yang lebih ketat untuk semua action akhir
- [x] validasi mandatory checklist untuk jenis pekerjaan tertentu
- [x] validasi mandatory failure/RCA untuk breakdown tertentu

### F3. Schedule Logic

- [x] history atau audit yang lebih eksplisit untuk reschedule
- [x] support schedule source yang lebih lengkap
- [x] due generation untuk trigger meter/condition yang lebih matang

### F4. Attachment Logic

- [x] immutable file event trail
- [ ] legal hold / retention awareness bila domain dokumen berkembang
- [x] secure download pattern

### F5. Asset Lifecycle Logic

- [x] assignment return
- [x] component relationship / component install-remove flow
- [x] lifecycle review and retirement recommendation

## G. Backend-to-Frontend Impact

Item backlog berikut akan paling memengaruhi frontend bila dikerjakan:

### Dampak tinggi ke workflow UI

- contract/warranty/SLA validation
- work order hold/resume/cancel
- attachment download/versioning
- component replacement analytics dan install-remove history visualization

### Dampak tinggi ke dashboard/report UI

- SLA snapshots
- vendor scorecard
- first-time fix rate
- replacement recommendation
- lease/warranty expiry monitoring

## H. Recommended Execution Order

Urutan yang paling masuk akal dari sisi engineering:

### Wave 1

- work order hold/resume/cancel
- assignment return
- attachment download/versioning dasar

### Wave 2

- maintenance contract master
- asset-to-contract link
- warranty master
- triage entitlement validation
- SLA snapshot foundation

### Wave 3

- vendor personnel
- part requirements
- maintenance skills
- richer work order decision rules

### Wave 4

- lease
- software license
- replacement analytics dan SAP integration preparation

### Wave 5

- SAP integration
- predictive maintenance
- advanced reliability optimization

## I. Definition of Ready untuk Fase Berikutnya

Sebelum lanjut ke domain besar berikutnya, idealnya pastikan:

- state machine tiap entitas sudah dibakukan
- role dan permission per action sudah jelas
- source master employee/vendor/item disepakati
- policy attachment dan retention disepakati
- boundary integrasi SAP B1 diputuskan
- sample scenario bisnis untuk feature baru sudah tersedia
