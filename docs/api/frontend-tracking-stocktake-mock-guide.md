# Frontend Tracking & Stocktake Mock Guide

Dokumen ini menjelaskan artifact mock khusus frontend untuk domain
`Tracking & Stocktake`.

Tanggal acuan: **Tuesday, July 28, 2026**.

## 1. File Mock

Gunakan file ini:

- [frontend_tracking_stocktake_mocks.json](/D:/projek/fastapi-asset/artifacts/frontend_tracking_stocktake_mocks.json)

File ini adalah ekstraksi dari:

- `artifacts/frontend_endpoint_samples.json`

Isi file mock ini:

- `seed_entities` penting untuk tracking & stocktake
- sample request/response live untuk endpoint tracking
- sample request/response live untuk endpoint stocktake
- sample report live untuk discrepancy dan unverified assets

## 2. Seed Entities yang Penting

Field yang sudah tersedia:

- `asset_id`
- `asset_transfer_id`
- `stocktake_id`
- `origin_location_id`
- `destination_location_id`
- `asset_tag_number`
- `auth_user_id`

Catatan:

- `stocktake_id` di artifact ini adalah ID sesi stocktake yang dipakai oleh
  route `/api/v1/stocktakes/{stocktake_session_id}`

## 3. Sample yang Bisa Dipakai per Halaman

### 3.1 Tracking Timeline

Gunakan sample:

- `create tracking scan event`
- `create tracking scan event batch`
- `get asset tracking timeline`

UI yang cocok:

- timeline scan
- verification list
- location match / mismatch badge

### 3.2 Stocktake List

Gunakan sample:

- `create stocktake session`
- `list stocktakes`

UI yang cocok:

- status chip
- planned vs started vs completed
- expected item count
- result count

### 3.3 Stocktake Detail

Gunakan sample:

- `get stocktake session`
- `start stocktake session`
- `scan stocktake session`
- `complete stocktake session`
- `approve stocktake session`

UI yang cocok:

- header session
- expected items table
- results table
- status workflow

### 3.4 Discrepancy Dashboard

Gunakan sample:

- `get location discrepancies report`
- `get missing assets report`
- `get unverified assets report`

UI yang cocok:

- KPI cards
- discrepancy table
- missing asset table
- aging unverified table

## 4. Alur Frontend yang Bisa Disimulasikan Sekarang

### Flow A. Tracking saja

1. render tracking timeline dari `get asset tracking timeline`
2. render scan event card dari `create tracking scan event`
3. render batch scan feedback dari `create tracking scan event batch`

### Flow B. Stocktake end-to-end

1. render list stocktake
2. buka detail stocktake dengan `stocktake_id`
3. render state sebelum start
4. render state sesudah start
5. render scan result
6. render state sesudah complete
7. render state sesudah approve

### Flow C. Verification dashboard

1. render location discrepancies
2. render missing assets
3. render unverified assets

## 5. Kenapa File Ini Dibuat

Sebelumnya sample tracking & stocktake memang tersebar di artifact besar.

Dengan file ini, frontend bisa:

- bekerja dengan mock yang lebih kecil dan fokus
- tidak perlu mencari label sample satu per satu
- langsung memakai ID seed yang relevan

## 6. Status

Domain `Tracking & Stocktake` pada backend **sudah bukan placeholder**.

Yang disediakan file ini adalah:

- mock frontend yang dikurasi dari response live backend
- referensi praktis agar implementasi UI lebih cepat
