# Implementation Roadmap

Dokumen ini menurunkan `implementation-gap-checklist.md` menjadi backlog
engineering yang lebih siap eksekusi.

Tanggal acuan roadmap: **Monday, July 27, 2026**.

Tujuan dokumen ini:

- menyusun prioritas implementasi backend per sprint;
- menjelaskan dependency teknis dan bisnis;
- membantu menjaga sinkronisasi backend, frontend, dan testing.

## Asumsi Dasar

- fondasi backend saat ini stabil dan smoke seed lulus `115/115`
- frontend sudah memiliki referensi endpoint, seed samples, dan blueprint fungsional
- setiap sprint di bawah ini diasumsikan fokus backend terlebih dahulu
- testing minimal tiap sprint adalah unit test + live smoke yang relevan

## Prioritas Umum

Urutan prioritas disusun dengan prinsip:

1. tutup gap pada workflow operasional yang sudah aktif
2. tambahkan entitlement/contract logic yang memengaruhi keputusan bisnis
3. perluas domain baseline besar setelah alur inti stabil
4. masuk ke integrasi SAP dan optimization setelah domain operasional matang

## Sprint 1

Tema:

- menyempurnakan workflow operasional inti yang sudah ada

Target utama:

- work order `hold`
- work order `resume`
- work order `cancel`
- assignment return
- attachment download dasar

Deliverable backend:

- command endpoint baru untuk `hold/resume/cancel`
- command endpoint `POST /assignments/{assignment_id}/return`
- endpoint download attachment/file
- penyesuaian state machine dan validation rules terkait
- update dokumen frontend bila status/action baru muncul

Dependency:

- definisi state machine work order final
- definisi business rule assignment return
- keputusan mekanisme secure file download

Definition of Done:

- command endpoint tersedia
- state invalid mengembalikan error code yang konsisten
- smoke test diperluas untuk status baru bila memungkinkan
- frontend reference diperbarui

## Sprint 2

Tema:

- entitlement foundation

Target utama:

- maintenance contracts
- maintenance contract assets
- warranty master
- triage validation contract/warranty

Deliverable backend:

- modul `maintenance_contracts`
- modul `warranties`
- relasi asset ke contract/warranty
- validasi coverage saat `triage_request`
- validasi coverage saat `convert_request_to_work_order`

Dependency:

- keputusan model data contract/warranty final
- business rules cakupan internal vs vendor
- aturan conflict bila contract dan warranty sama-sama aktif

Definition of Done:

- request dapat menilai entitlement minimum
- traceability contract/warranty tersedia pada request/work order
- test scenario mencakup request yang covered dan not covered

## Sprint 3

Tema:

- SLA dan attachment maturity

Target utama:

- SLA snapshot foundation
- SLA escalation foundation
- attachment version history
- replace/upload new file version

Deliverable backend:

- struktur `maintenance_sla_snapshots`
- kalkulasi snapshot saat request penting berubah status
- endpoint list version file
- endpoint upload versi baru
- audit trail perubahan file yang lebih eksplisit

Dependency:

- mapping SLA dari priority dan contract
- keputusan retention dan version policy file

Definition of Done:

- SLA data bisa dipakai dashboard dan audit
- file versioning bisa dipakai frontend dokumen
- sample response baru tersedia untuk frontend

## Sprint 4

Tema:

- maintenance execution enrichment

Target utama:

- vendor personnel
- part requirements
- maintenance skills
- employee maintenance skills
- validasi skill terhadap assignment

Deliverable backend:

- master vendor personnel
- planned part requirement per work order
- master maintenance skill
- relasi employee skill
- skill validation saat assignment

Dependency:

- sumber master employee
- keputusan apakah vendor personnel disinkronkan dari sistem lain
- definisi mandatory skills per work order atau maintenance type

Definition of Done:

- assignment lebih realistis
- spare part bisa dibedakan antara planned dan actual
- readiness work order meningkat

## Sprint 5

Tema:

- lifecycle dan asset entitlement expansion

Target utama:

- lifecycle reviews
- retirement requests
- warranty claims
- expiry monitoring untuk warranty/contract

Deliverable backend:

- lifecycle review API
- retirement request API
- warranty claim API
- expiry monitoring query/report sederhana

Dependency:

- keputusan approval flow retirement
- keputusan hubungan ke proses finance/SAP

Definition of Done:

- frontend dapat melihat asset mendekati akhir lifecycle
- proses warranty claim tercatat
- lifecycle flow tidak merusak asset registry inti

## Sprint 6

Tema:

- lease dan software asset domain

Target utama:

- lease contracts
- lease items
- lease payments
- software licenses
- software license assignments
- software license release

Deliverable backend:

- modul `leases`
- modul `software_licenses`
- rules overlap dan capacity checks

Dependency:

- keputusan apakah software asset masuk fase ini atau dipisah
- definisi relasi ke business partner/lessor/publisher

Definition of Done:

- asset leased dan software licensed bisa direkam terpisah dari asset ownership biasa
- release/capacity checks tervalidasi

## Sprint 7

Tema:

- SAP integration foundation

Target utama:

- integration mappings
- reconciliation API
- integration error log
- retry integration error

Deliverable backend:

- struktur mapping internal ke SAP
- API monitoring error integrasi
- retry operation untuk error tertentu
- dasar integration outbox bila dipilih

Dependency:

- keputusan arsitektur integrasi SAP B1
- boundary writeback yang diizinkan
- kesepakatan ownership data master finance/inventory

Definition of Done:

- kesalahan integrasi terlihat dan bisa diretry
- reconciliation bisa dijalankan terkontrol

## Sprint 8

Tema:

- maintenance optimization dan analytical maturity

Target utama:

- predictive/condition-based trigger
- vendor scorecard
- first-time fix rate
- replacement recommendation

Deliverable backend:

- trigger logic lanjutan
- report vendor performance
- KPI reliability tambahan
- dasar recommendation engine sederhana

Dependency:

- definisi bisnis untuk MTBF/MTTR/FTFR
- kecukupan data historis
- agreement atas formula recommendation

Definition of Done:

- dashboard maintenance menjadi lebih manajerial
- reliability analytics tidak hanya deskriptif tetapi mulai preskriptif

## Rekomendasi Eksekusi Teknis

### Track A. Workflow Stability

Kerjakan lebih dulu:

- work order hold/resume/cancel
- assignment return
- attachment download

Alasan:

- risikonya rendah
- dampaknya cepat terasa di frontend
- membantu menstabilkan state machine inti

### Track B. Entitlement Core

Kerjakan sesudah Track A:

- maintenance contracts
- warranties
- SLA snapshots

Alasan:

- ini fondasi keputusan bisnis untuk request/work order
- akan memengaruhi struktur UI dan report

### Track C. Operational Enrichment

Kerjakan setelah entitlement cukup matang:

- vendor personnel
- part requirements
- skills

Alasan:

- meningkatkan kualitas execution, bukan hanya pencatatan

### Track D. Extended Domains

Kerjakan setelah core maintenance stabil:

- lifecycle review
- retirement
- lease
- software license
- depreciation

### Track E. Integration and Optimization

Kerjakan terakhir:

- SAP integration
- predictive maintenance
- optimization analytics

## Frontend Coupling Notes

Sprint yang paling banyak mengubah frontend:

- Sprint 1: status/action baru pada work order dan assignment
- Sprint 2: field entitlement pada request/work order
- Sprint 3: SLA widget dan attachment document UI
- Sprint 4: team/skill/planned-part UI
- Sprint 5: lifecycle and warranty screens
- Sprint 6: lease/software menus baru

## Testing Strategy by Sprint

### Minimum untuk setiap sprint

- unit test untuk service logic baru
- update smoke test jika feature masuk jalur utama
- review dokumentasi frontend bila contract berubah

### Tambahan untuk sprint tertentu

- Sprint 2 dan 3:
  - integration-style tests untuk entitlement dan SLA
- Sprint 7:
  - retry/idempotency tests
- Sprint 8:
  - report calculation tests

## Saran Cara Mulai Langsung di Codebase Ini

Urutan implementasi konkret yang paling aman:

1. tambahkan enum/status baru dan schema payload untuk `hold/resume/cancel`
2. implementasikan service + routes work order command baru
3. tambahkan endpoint assignment return
4. tambahkan endpoint attachment download
5. sesudah itu baru buka modul baru `warranties` dan `maintenance_contracts`

## Deliverable Documents yang Perlu Selalu Diupdate

Setiap sprint yang mengubah API sebaiknya ikut mengubah:

- `docs/api/frontend-api-reference.md`
- `docs/api/frontend-page-endpoint-map.md`
- `docs/api/frontend-functional-blueprint.md`
- `docs/implementation-gap-checklist.md`

Jika ada sample baru:

- rerun `scripts/smoke_seed_api.py`
- refresh:
  - `artifacts/seed_smoke_results.json`
  - `artifacts/frontend_endpoint_samples.json`
  - `artifacts/postman_seed_environment.json`
  - `artifacts/postman_seed_collection.json`
