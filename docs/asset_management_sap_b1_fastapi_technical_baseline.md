# Baseline Teknis Asset Management Terintegrasi SAP Business One

## 1. Informasi dokumen

| Atribut | Nilai |
|---|---|
| Nama sistem | Asset Management Application |
| Backend | FastAPI |
| Database | PostgreSQL |
| Integrasi utama | SAP Business One |
| Jenis dokumen | Baseline arsitektur data dan implementasi |
| Status | Konsep awal untuk validasi dan pengembangan |
| Versi dokumen | 0.1.0 |

Dokumen ini menjadi acuan awal untuk membangun aplikasi **operational asset lifecycle management** yang melengkapi fungsi Fixed Assets pada SAP Business One (SAP B1).

Aplikasi tidak dimaksudkan menggantikan fungsi akuntansi aset tetap SAP B1. SAP B1 tetap menjadi sumber kebenaran untuk kapitalisasi, depresiasi, nilai buku, dan posting finansial. Aplikasi Asset Management menjadi sumber kebenaran untuk identitas operasional aset, lokasi aktual, pengguna/pemegang, garansi, sewa, lisensi software, kontrak pemeliharaan, kondisi, dan lifecycle.

---

## 2. Tujuan desain

Desain ini harus memenuhi kebutuhan berikut:

1. Menyediakan satu registry untuk aset milik perusahaan, aset sewa, pinjaman, dan aset milik mitra.
2. Mendukung aset tetap yang memiliki garansi, depresiasi, lifetime, serta histori nilai.
3. Mendukung aset yang memiliki software dan lisensi dengan expiry, subscription, seat, serta update entitlement.
4. Mendukung kontrak pemeliharaan yang dapat mencakup banyak aset dan memiliki SLA.
5. Menyimpan histori lokasi, pemegang, kondisi, status, kepemilikan, dan perubahan lifecycle.
6. Menghubungkan entitas lokal dengan object dan dokumen SAP B1 tanpa membuat model domain bergantung langsung kepada nama tabel fisik SAP.
7. Menyediakan struktur modular yang dapat diterapkan menggunakan FastAPI, SQLAlchemy, Alembic, dan PostgreSQL.
8. Menjamin auditability, idempotency integrasi, dan konsistensi transaksi.

---

## 3. Batas tanggung jawab sistem

### 3.1 SAP Business One sebagai system of record

SAP B1 bertanggung jawab atas:

- Asset Master Data finansial;
- Asset Class finansial;
- Depreciation Area;
- Depreciation Type atau metode penyusutan;
- kapitalisasi dan tambahan kapitalisasi;
- A/P Invoice terkait perolehan aset;
- depresiasi terencana dan depresiasi terposting;
- nilai buku dan akumulasi depresiasi;
- retirement atau disposal yang menghasilkan posting finansial;
- journal entry dan rekonsiliasi general ledger.

### 3.2 Aplikasi Asset Management sebagai system of record

Aplikasi bertanggung jawab atas:

- asset registry operasional;
- barcode, QR code, serial number, dan spesifikasi teknis;
- struktur parent asset, subasset, dan komponen;
- lokasi aktual dan histori perpindahan;
- custodian, pengguna, technical PIC, dan histori assignment;
- kepemilikan mitra, aset sewa, pinjaman, dan partner placement;
- garansi dan warranty claim;
- kontrak pemeliharaan dan SLA;
- software product, license entitlement, seat, serta installation;
- technical lifetime, economic lifetime, replacement planning;
- dokumen, foto, sertifikat, serta audit trail;
- notifikasi expiry dan kegiatan lifecycle.

### 3.3 Matriks otoritas data

| Data | System of Record | Arah utama sinkronisasi |
|---|---|---|
| Nilai kapitalisasi | SAP B1 | SAP B1 → AMS |
| Depresiasi dan nilai buku | SAP B1 | SAP B1 → AMS |
| A/P Invoice | SAP B1 | SAP B1 → AMS |
| Asset Class finansial | SAP B1 | SAP B1 → AMS |
| Business Partner | SAP B1, bila telah tersedia | SAP B1 → AMS |
| Identitas teknis aset | AMS | AMS internal atau AMS → SAP B1 bila diperlukan |
| Lokasi aktual | AMS | AMS |
| Custodian dan pengguna | AMS | AMS |
| Warranty | AMS | AMS |
| Lease operational detail | AMS | AMS |
| Maintenance contract coverage | AMS | AMS |
| Software installation | AMS | AMS |
| Lifecycle dan replacement plan | AMS | AMS |
| Disposal finansial | SAP B1 | Permintaan AMS, posting final di SAP B1 |

> **AMS** dalam dokumen ini berarti Asset Management System/Application.

---

## 4. Prinsip desain data

### 4.1 `assets` hanya menyimpan identity dan current state

Tabel `assets` merupakan pusat registry, tetapi tidak boleh menjadi tabel besar yang menampung seluruh data finansial, kontrak, warranty, software, dan histori.

Data berikut harus dipisahkan:

- data berulang;
- data yang memiliki periode berlaku;
- data yang dapat berubah;
- data yang dimiliki banyak aset;
- data yang memiliki audit atau histori;
- data yang berasal dari SAP B1.

### 4.2 Current state dan history

Field current state boleh disimpan di `assets` untuk mempercepat query:

- `current_location_id`;
- `asset_status`;
- `condition_status`;
- `current_primary_custodian_id`.

Namun perubahan resmi harus selalu menghasilkan baris baru pada tabel history atau transaction. Pembaruan current state dan penulisan history dilakukan dalam satu database transaction.

### 4.3 Master, transaction, history, dan integration

| Jenis | Contoh |
|---|---|
| Master/reference | `asset_categories`, `asset_classes`, `service_levels` |
| Identity/current state | `assets` |
| Transaction | `asset_acquisitions`, `asset_transfers`, `asset_retirements` |
| Periodic/temporal | `asset_ownerships`, `asset_assignments` |
| History/snapshot | `asset_status_histories`, `asset_value_snapshots` |
| Junction | `maintenance_contract_assets`, `asset_lease_items` |
| Integration | `sap_integration_mappings`, `integration_outbox` |
| Audit | `audit_logs` |

### 4.4 Aturan umum primary key dan waktu

- Gunakan UUID untuk primary key aplikasi.
- PostgreSQL dapat menggunakan `gen_random_uuid()`.
- Gunakan `TIMESTAMPTZ`, bukan `TIMESTAMP`, untuk event waktu.
- Gunakan `DATE` untuk tanggal bisnis yang tidak memiliki jam.
- Semua tabel bisnis minimal memiliki `created_at`, `created_by`, `updated_at`, dan `updated_by`.
- Gunakan soft delete hanya untuk data yang memang boleh dinonaktifkan. Transaksi dan history tidak boleh dihapus secara normal.

### 4.5 Aturan nilai uang

- Gunakan `NUMERIC(20,4)` untuk nilai uang.
- Simpan `currency_code CHAR(3)`.
- Jika transaksi bukan dalam base currency, simpan `exchange_rate` dan `base_currency_amount`.
- Jangan menggunakan `FLOAT` atau `DOUBLE PRECISION` untuk nilai finansial.

### 4.6 Aturan penghapusan foreign key

| Relasi | Aturan umum |
|---|---|
| Master yang sudah dipakai | `ON DELETE RESTRICT` |
| Child murni yang tidak bermakna tanpa parent | `ON DELETE CASCADE`, hanya bila parent belum menjadi transaksi final |
| History, posting, snapshot, mapping SAP | `ON DELETE RESTRICT` |
| Referensi opsional | `ON DELETE SET NULL`, bila kehilangan referensi masih dapat diaudit |

---

## 5. Domain model

Model dibagi ke dalam bounded context berikut:

1. Organization and Partner;
2. Asset Registry;
3. Location and Assignment;
4. Acquisition and Financial Reference;
5. Warranty;
6. Lease;
7. Software License;
8. Maintenance Contract;
9. Lifecycle and Meter;
10. Document;
11. SAP B1 Integration;
12. Audit and Notification.

---

## 6. ERD konseptual

```mermaid
erDiagram
    ASSET_CATEGORIES ||--o{ ASSETS : classifies
    ASSET_CLASSES ||--o{ ASSETS : financial_class
    ASSETS ||--o{ ASSETS : parent_of
    ASSETS ||--o{ ASSET_OWNERSHIPS : has
    BUSINESS_PARTNERS ||--o{ ASSET_OWNERSHIPS : owns
    ASSETS ||--o{ ASSET_ACQUISITIONS : capitalized_by
    BUSINESS_PARTNERS ||--o{ ASSET_ACQUISITIONS : supplies
    ASSETS ||--o{ ASSET_ASSIGNMENTS : assigned
    EMPLOYEES ||--o{ ASSET_ASSIGNMENTS : receives
    ASSETS ||--o{ ASSET_LOCATION_HISTORIES : moves
    ASSET_LOCATIONS ||--o{ ASSET_LOCATION_HISTORIES : referenced_by
    ASSETS ||--o{ ASSET_STATUS_HISTORIES : changes
```

```mermaid
erDiagram
    ASSETS ||--o{ ASSET_WARRANTIES : covered_by
    ASSET_WARRANTIES ||--o{ ASSET_WARRANTY_CLAIMS : has
    BUSINESS_PARTNERS ||--o{ ASSET_WARRANTIES : provides
    ASSETS ||--o{ MAINTENANCE_CONTRACT_ASSETS : covered
    MAINTENANCE_CONTRACTS ||--o{ MAINTENANCE_CONTRACT_ASSETS : includes
    BUSINESS_PARTNERS ||--o{ MAINTENANCE_CONTRACTS : vendor
    SERVICE_LEVELS ||--o{ MAINTENANCE_CONTRACTS : governs
    ASSETS ||--o{ ASSET_LEASE_ITEMS : leased_item
    ASSET_LEASE_CONTRACTS ||--o{ ASSET_LEASE_ITEMS : includes
    ASSET_LEASE_CONTRACTS ||--o{ ASSET_LEASE_PAYMENTS : schedules
```

```mermaid
erDiagram
    SOFTWARE_PRODUCTS ||--o{ SOFTWARE_LICENSES : licensed_as
    SOFTWARE_LICENSES ||--o{ SOFTWARE_INSTALLATIONS : installed
    ASSETS ||--o{ SOFTWARE_INSTALLATIONS : hosts
    SOFTWARE_LICENSES ||--o{ SOFTWARE_LICENSE_ASSIGNMENTS : assigned
    EMPLOYEES ||--o{ SOFTWARE_LICENSE_ASSIGNMENTS : user
    ASSETS ||--o{ ASSET_DEPRECIATION_PARAMETERS : configured
    DEPRECIATION_AREAS ||--o{ ASSET_DEPRECIATION_PARAMETERS : area
    DEPRECIATION_METHODS ||--o{ ASSET_DEPRECIATION_PARAMETERS : method
    ASSETS ||--o{ ASSET_VALUE_SNAPSHOTS : valued
```

```mermaid
erDiagram
    ASSETS ||--|| ASSET_LIFECYCLE_PROFILES : profile
    ASSETS ||--o{ ASSET_LIFECYCLE_REVIEWS : reviewed
    ASSETS ||--o{ ASSET_METERS : measured
    ASSET_METERS ||--o{ ASSET_METER_READINGS : records
    DOCUMENTS ||--o{ DOCUMENT_LINKS : linked
    ASSETS ||--o{ SAP_INTEGRATION_MAPPINGS : mapped
    ASSETS ||--o{ AUDIT_LOGS : audited
```

---

## 7. Organization dan business partner

### 7.1 `business_partners`

Satu master digunakan untuk supplier, manufacturer, lessor, warranty provider, maintenance vendor, insurer, dan software publisher.

```text
business_partners
-----------------
id UUID PK
partner_code VARCHAR(50) UNIQUE
partner_name VARCHAR(200)
tax_number VARCHAR(100) NULL
email VARCHAR(150) NULL
phone VARCHAR(50) NULL
address TEXT NULL
sap_card_code VARCHAR(50) NULL
is_active BOOLEAN
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

### 7.2 `business_partner_roles`

```text
business_partner_roles
----------------------
id UUID PK
business_partner_id UUID FK
role_type VARCHAR(30)
valid_from DATE NULL
valid_to DATE NULL
```

Nilai `role_type`:

```text
SUPPLIER
MANUFACTURER
LESSOR
MAINTENANCE_VENDOR
WARRANTY_PROVIDER
INSURER
SOFTWARE_PUBLISHER
```

Constraint:

```sql
UNIQUE (business_partner_id, role_type, valid_from)
```

### 7.3 Organization master

Tabel minimum:

- `companies`;
- `branches`;
- `departments`;
- `cost_centers`;
- `projects`;
- `employees`.

Master tersebut dapat disinkronkan dari SAP B1 atau HR system sesuai sumber data yang disepakati.

---

## 8. Asset Registry

### 8.1 `asset_categories`

Kategori merupakan klasifikasi operasional, misalnya kendaraan, laptop, mesin, gedung, dan furniture.

```text
asset_categories
----------------
id UUID PK
category_code VARCHAR(50) UNIQUE
category_name VARCHAR(150)
parent_category_id UUID FK NULL
description TEXT NULL
is_active BOOLEAN
```

Relasi kategori bersifat hierarchy:

```text
asset_categories.id → asset_categories.parent_category_id
```

### 8.2 `asset_classes`

Asset Class merupakan klasifikasi finansial yang dikaitkan dengan konfigurasi SAP B1.

```text
asset_classes
-------------
id UUID PK
class_code VARCHAR(50) UNIQUE
class_name VARCHAR(150)
description TEXT NULL
sap_asset_class_code VARCHAR(50) NULL
default_useful_life_months INTEGER NULL
is_depreciable BOOLEAN
is_active BOOLEAN
```

Kategori dan class tidak disatukan karena tujuan keduanya berbeda:

```text
Category    : Laptop
Asset Class : IT Equipment - 4 Years
```

### 8.3 `assets`

```text
assets
------
id UUID PK
asset_code VARCHAR(50) UNIQUE
asset_name VARCHAR(200)
description TEXT NULL

asset_category_id UUID FK
asset_class_id UUID FK NULL
parent_asset_id UUID FK NULL

asset_type VARCHAR(30)
asset_status VARCHAR(30)
condition_status VARCHAR(30)
criticality_level VARCHAR(20)

serial_number VARCHAR(150) NULL
manufacturer_id UUID FK NULL
brand VARCHAR(100) NULL
model VARCHAR(100) NULL
manufacture_year INTEGER NULL

company_id UUID FK
branch_id UUID FK NULL
current_location_id UUID FK NULL
current_primary_custodian_id UUID FK NULL

barcode VARCHAR(100) NULL
qr_code VARCHAR(200) NULL
tag_number VARCHAR(100) NULL
tracking_status VARCHAR(20) DEFAULT 'TRACKED'
last_verified_at TIMESTAMPTZ NULL
last_verified_location_id UUID FK NULL

in_service_date DATE NULL
retirement_date DATE NULL

sap_asset_code VARCHAR(50) NULL
sap_item_code VARCHAR(50) NULL

version_no INTEGER DEFAULT 1
created_at TIMESTAMPTZ
created_by UUID
updated_at TIMESTAMPTZ
updated_by UUID
```

Nilai contoh `asset_type`:

```text
FIXED_ASSET
LOW_VALUE_ASSET
LEASED_ASSET
PARTNER_ASSET
BORROWED_ASSET
RIGHT_OF_USE_ASSET
INTANGIBLE_ASSET
COMPONENT
```

Nilai contoh `asset_status`:

```text
DRAFT
REGISTERED
IN_STOCK
IN_SERVICE
UNDER_MAINTENANCE
IDLE
LOST
DAMAGED
RETIRED
DISPOSED
RETURNED
```

Nilai contoh `condition_status`:

```text
NEW
GOOD
FAIR
POOR
CRITICAL
UNSERVICEABLE
```

Constraint penting:

```sql
CHECK (parent_asset_id IS NULL OR parent_asset_id <> id);
CHECK (manufacture_year IS NULL OR manufacture_year BETWEEN 1900 AND 2200);
CHECK (retirement_date IS NULL OR in_service_date IS NULL
       OR retirement_date >= in_service_date);
```

Validasi circular hierarchy dilakukan pada service layer atau menggunakan trigger/recursive CTE.

### 8.4 Custom attributes

Spesifikasi antar-kategori berbeda. Hindari menambahkan semua field teknis ke tabel `assets`.

```text
asset_attribute_definitions
---------------------------
id UUID PK
asset_category_id UUID FK
attribute_code VARCHAR(50)
attribute_name VARCHAR(150)
data_type VARCHAR(20)
unit_of_measure VARCHAR(30) NULL
is_required BOOLEAN
validation_rule JSONB NULL

asset_attribute_values
----------------------
id UUID PK
asset_id UUID FK
attribute_definition_id UUID FK
value_text TEXT NULL
value_number NUMERIC(20,6) NULL
value_date DATE NULL
value_boolean BOOLEAN NULL
value_json JSONB NULL
```

Constraint:

```sql
UNIQUE (asset_id, attribute_definition_id)
```

Service harus memastikan hanya satu kolom nilai yang digunakan sesuai `data_type`.

---

## 9. Kepemilikan aset

### 9.1 `asset_ownerships`

```text
asset_ownerships
----------------
id UUID PK
asset_id UUID FK
owner_type VARCHAR(30)
owner_partner_id UUID FK NULL
owner_company_id UUID FK NULL
ownership_percentage NUMERIC(8,4)
effective_from DATE
effective_to DATE NULL
source_reference VARCHAR(150) NULL
notes TEXT NULL
```

Nilai `owner_type`:

```text
COMPANY
PARTNER
JOINT
LESSOR
GOVERNMENT
OTHER
```

Aturan:

- `owner_partner_id` atau `owner_company_id` wajib terisi sesuai `owner_type`;
- `ownership_percentage > 0` dan `<= 100`;
- total persentase untuk satu aset pada periode yang sama tidak boleh melebihi 100%;
- tidak boleh ada dua kepemilikan penuh yang periodenya tumpang tindih.

Validasi overlap sebaiknya menggunakan PostgreSQL exclusion constraint dengan `daterange`.

---

## 10. Location, transfer, dan assignment

### 10.1 `asset_locations`

```text
asset_locations
---------------
id UUID PK
location_code VARCHAR(50) UNIQUE
location_name VARCHAR(150)
location_type VARCHAR(30)
parent_location_id UUID FK NULL
company_id UUID FK
branch_id UUID FK NULL
warehouse_code VARCHAR(50) NULL
bin_location_code VARCHAR(50) NULL
latitude NUMERIC(10,7) NULL
longitude NUMERIC(10,7) NULL
is_active BOOLEAN
```

Contoh hierarchy:

```text
Head Office
└── Building A
    └── Floor 2
        └── IT Room
```

### 10.2 `asset_transfers`

`asset_transfers` menjadi dokumen bisnis perpindahan.

```text
asset_transfers
---------------
id UUID PK
transfer_number VARCHAR(50) UNIQUE
transfer_date TIMESTAMPTZ
transfer_type VARCHAR(30)
status VARCHAR(20)
movement_purpose VARCHAR(30)
is_permanent BOOLEAN
expected_return_at TIMESTAMPTZ NULL
from_location_id UUID FK NULL
to_location_id UUID FK
from_department_id UUID FK NULL
to_department_id UUID FK NULL
requested_by UUID
approved_by UUID NULL
approved_at TIMESTAMPTZ NULL
dispatched_by UUID NULL
dispatched_at TIMESTAMPTZ NULL
received_by UUID NULL
received_at TIMESTAMPTZ NULL
reason TEXT NULL
```

```text
asset_transfer_items
--------------------
id UUID PK
asset_transfer_id UUID FK
asset_id UUID FK
previous_custodian_id UUID FK NULL
new_custodian_id UUID FK NULL
handover_condition VARCHAR(30)
dispatch_scan_event_id UUID FK NULL
receipt_scan_event_id UUID FK NULL
item_status VARCHAR(20)
notes TEXT NULL
```

Constraint:

```sql
UNIQUE (asset_transfer_id, asset_id)
```

### 10.3 `asset_location_histories`

```text
asset_location_histories
------------------------
id UUID PK
asset_id UUID FK
from_location_id UUID FK NULL
to_location_id UUID FK
effective_at TIMESTAMPTZ
ended_at TIMESTAMPTZ NULL
transfer_id UUID FK NULL
reason TEXT NULL
recorded_by UUID
```

### 10.4 `asset_assignments`

```text
asset_assignments
-----------------
id UUID PK
asset_id UUID FK
assignment_type VARCHAR(30)
employee_id UUID FK NULL
department_id UUID FK NULL
assigned_at TIMESTAMPTZ
expected_return_date DATE NULL
returned_at TIMESTAMPTZ NULL
handover_document_id UUID FK NULL
accepted_by_employee_at TIMESTAMPTZ NULL
released_by_employee_at TIMESTAMPTZ NULL
assignment_status VARCHAR(20)
notes TEXT NULL
```

Nilai `assignment_type`:

```text
PRIMARY_CUSTODIAN
USER
TECHNICAL_PIC
DEPARTMENT_CONTROL
TEMPORARY_BORROWER
```

Aturan:

- hanya satu `PRIMARY_CUSTODIAN` aktif per aset;
- `employee_id` atau `department_id` harus terisi;
- `returned_at >= assigned_at`;
- assignment aktif ditandai `assignment_status = 'ACTIVE'` dan `returned_at IS NULL`;
- assignment kepada karyawan baru efektif setelah penerima mengonfirmasi serah terima;
- `PRIMARY_CUSTODIAN` adalah penanggung jawab administratif, sedangkan `USER` adalah pemakai aktual dan keduanya boleh berbeda;
- perubahan custodian harus berasal dari transfer/serah-terima yang dapat diaudit.

### 10.5 Transaksi pemindahan

Satu pemindahan yang telah disetujui harus mengeksekusi:

1. validasi status asset dan lokasi asal;
2. mengunci row aset menggunakan `SELECT ... FOR UPDATE`;
3. membuat `asset_transfer_items`;
4. menutup histori lokasi aktif;
5. membuat histori lokasi baru;
6. menutup assignment lama bila custodian berubah;
7. membuat assignment baru;
8. memperbarui current state pada `assets`;
9. menulis audit log;
10. commit sebagai satu transaksi.

---

## 11. Akuisisi dan referensi finansial

### 11.1 `asset_acquisitions`

Satu aset dapat memiliki perolehan awal dan tambahan kapitalisasi.

```text
asset_acquisitions
------------------
id UUID PK
asset_id UUID FK
acquisition_type VARCHAR(30)
acquisition_date DATE
capitalization_date DATE NULL
supplier_id UUID FK NULL

quantity NUMERIC(20,4) DEFAULT 1
unit_price NUMERIC(20,4)
additional_cost NUMERIC(20,4) DEFAULT 0
capitalized_cost NUMERIC(20,4)
currency_code CHAR(3)
exchange_rate NUMERIC(20,8) NULL
base_currency_amount NUMERIC(20,4) NULL

source_document_type VARCHAR(30) NULL
source_document_number VARCHAR(100) NULL
sap_doc_entry INTEGER NULL
sap_doc_num INTEGER NULL
sap_trans_id INTEGER NULL
```

Nilai `acquisition_type`:

```text
PURCHASE
TRANSFER
DONATION
CONSTRUCTION
INTERNAL_PRODUCTION
LEASE_RECOGNITION
OPENING_BALANCE
CAPITALIZED_IMPROVEMENT
```

### 11.2 Depreciation master

```text
depreciation_areas
------------------
id UUID PK
area_code VARCHAR(30) UNIQUE
area_name VARCHAR(100)
area_type VARCHAR(30)
posts_to_gl BOOLEAN
sap_area_code VARCHAR(30) NULL
is_active BOOLEAN

depreciation_methods
--------------------
id UUID PK
method_code VARCHAR(30) UNIQUE
method_name VARCHAR(100)
calculation_method VARCHAR(30)
rate_percent NUMERIC(10,6) NULL
period_control_method VARCHAR(30) NULL
sap_depreciation_type_code VARCHAR(30) NULL
is_active BOOLEAN
```

Nilai `calculation_method`:

```text
STRAIGHT_LINE
DECLINING_BALANCE
DOUBLE_DECLINING
SUM_OF_YEARS_DIGITS
UNITS_OF_PRODUCTION
NO_DEPRECIATION
MANUAL
```

### 11.3 `asset_depreciation_parameters`

```text
asset_depreciation_parameters
-----------------------------
id UUID PK
asset_id UUID FK
depreciation_area_id UUID FK
depreciation_method_id UUID FK
capitalization_date DATE
depreciation_start_date DATE
useful_life_months INTEGER
remaining_useful_life_months INTEGER
acquisition_cost NUMERIC(20,4)
residual_value NUMERIC(20,4)
depreciable_value NUMERIC(20,4)
depreciation_rate NUMERIC(10,6) NULL
expired_useful_life_months INTEGER DEFAULT 0
valid_from DATE
valid_to DATE NULL
sap_sync_status VARCHAR(30)
```

Constraint:

```sql
UNIQUE (asset_id, depreciation_area_id, valid_from);
CHECK (useful_life_months > 0);
CHECK (residual_value >= 0);
CHECK (depreciable_value >= 0);
CHECK (valid_to IS NULL OR valid_to >= valid_from);
```

Periode efektif pada asset dan depreciation area yang sama tidak boleh overlap.

### 11.4 `asset_value_snapshots`

```text
asset_value_snapshots
---------------------
id UUID PK
asset_id UUID FK
depreciation_area_id UUID FK
fiscal_year INTEGER
fiscal_period INTEGER
snapshot_date DATE
acquisition_cost NUMERIC(20,4)
capitalized_additions NUMERIC(20,4)
retirements NUMERIC(20,4)
transfers NUMERIC(20,4)
revaluation_amount NUMERIC(20,4)
planned_depreciation NUMERIC(20,4)
posted_depreciation NUMERIC(20,4)
accumulated_depreciation NUMERIC(20,4)
net_book_value NUMERIC(20,4)
sap_trans_id INTEGER NULL
source_synced_at TIMESTAMPTZ
```

Constraint:

```sql
UNIQUE (asset_id, depreciation_area_id, fiscal_year, fiscal_period);
CHECK (fiscal_period BETWEEN 1 AND 16);
```

Jumlah fiscal period harus menjadi konfigurasi perusahaan. Batas 16 hanya batas teknis awal dan perlu disesuaikan dengan konfigurasi SAP B1.

### 11.5 `asset_retirements`

```text
asset_retirements
-----------------
id UUID PK
asset_id UUID FK
retirement_number VARCHAR(50) UNIQUE
retirement_type VARCHAR(30)
request_date DATE
effective_date DATE NULL
status VARCHAR(20)
proceeds_amount NUMERIC(20,4) DEFAULT 0
buyer_partner_id UUID FK NULL
reason TEXT
approved_by UUID NULL
sap_retirement_doc_entry INTEGER NULL
sap_trans_id INTEGER NULL
```

Retirement tidak boleh menjadi final di AMS sebelum SAP B1 mengonfirmasi dokumen finansial, kecuali untuk aset non-finansial yang secara eksplisit tidak dikelola sebagai Fixed Asset di SAP B1.

---

## 12. Warranty

### 12.1 `asset_warranties`

```text
asset_warranties
----------------
id UUID PK
asset_id UUID FK
warranty_type VARCHAR(30)
provider_partner_id UUID FK NULL
provider_name VARCHAR(200) NULL
warranty_number VARCHAR(100) NULL
coverage_description TEXT
start_date DATE
end_date DATE
claim_deadline_days INTEGER NULL
parts_covered BOOLEAN
labor_covered BOOLEAN
onsite_service BOOLEAN
replacement_covered BOOLEAN
contact_person VARCHAR(150) NULL
contact_phone VARCHAR(50) NULL
contact_email VARCHAR(150) NULL
status VARCHAR(20)
```

Nilai `warranty_type`:

```text
MANUFACTURER
SUPPLIER
EXTENDED
COMPONENT
SERVICE
```

Status sebaiknya dihitung dari periode dan state transaksi:

```text
UPCOMING
ACTIVE
EXPIRING
EXPIRED
CANCELLED
CLAIMED
```

### 12.2 `asset_warranty_claims`

```text
asset_warranty_claims
---------------------
id UUID PK
warranty_id UUID FK
asset_id UUID FK
claim_number VARCHAR(100) UNIQUE
claim_date DATE
problem_description TEXT
claim_status VARCHAR(30)
resolution_description TEXT NULL
resolved_at TIMESTAMPTZ NULL
replacement_asset_id UUID FK NULL
cost_covered NUMERIC(20,4) NULL
cost_not_covered NUMERIC(20,4) NULL
```

Aturan:

- `claim.asset_id` harus sama dengan `warranty.asset_id`;
- claim date harus berada dalam periode yang diizinkan warranty dan claim deadline;
- biaya tidak boleh negatif;
- replacement asset tidak boleh sama dengan asset yang diklaim.

---

## 13. Lease dan partner asset

### 13.1 `asset_lease_contracts`

```text
asset_lease_contracts
---------------------
id UUID PK
contract_number VARCHAR(100) UNIQUE
lessor_partner_id UUID FK
lessee_company_id UUID FK NULL
lease_type VARCHAR(30)
accounting_treatment VARCHAR(30)
start_date DATE
end_date DATE
extension_option_end_date DATE NULL
billing_frequency VARCHAR(20)
payment_amount NUMERIC(20,4)
currency_code CHAR(3)
deposit_amount NUMERIC(20,4) DEFAULT 0
purchase_option_amount NUMERIC(20,4) NULL
auto_renewal BOOLEAN
notice_period_days INTEGER NULL
maintenance_included BOOLEAN
insurance_included BOOLEAN
tax_included BOOLEAN
status VARCHAR(20)
```

Nilai `lease_type`:

```text
OPERATING_LEASE
FINANCE_LEASE
RENTAL
BORROWED
PARTNER_PLACEMENT
RIGHT_OF_USE
```

Nilai `accounting_treatment`:

```text
EXPENSE_ONLY
RIGHT_OF_USE_ASSET
FINANCE_LEASE
OFF_BALANCE_SHEET
MANAGED_ASSET_ONLY
```

### 13.2 `asset_lease_items`

Tabel ini menjadi junction many-to-many antara kontrak dan aset.

```text
asset_lease_items
-----------------
id UUID PK
lease_contract_id UUID FK
asset_id UUID FK
lease_start_date DATE
lease_end_date DATE
monthly_amount NUMERIC(20,4) NULL
allocation_percentage NUMERIC(8,4) DEFAULT 100
return_condition TEXT NULL
returned_at TIMESTAMPTZ NULL
```

Constraint:

```sql
UNIQUE (lease_contract_id, asset_id, lease_start_date);
CHECK (allocation_percentage > 0 AND allocation_percentage <= 100);
CHECK (lease_end_date >= lease_start_date);
```

Periode item harus berada di dalam periode kontrak. Satu aset tidak boleh memiliki dua lease aktif yang saling overlap, kecuali business rule secara eksplisit mengizinkan co-leasing.

### 13.3 `asset_lease_payments`

```text
asset_lease_payments
--------------------
id UUID PK
lease_contract_id UUID FK
period_start DATE
period_end DATE
due_date DATE
principal_amount NUMERIC(20,4) DEFAULT 0
interest_amount NUMERIC(20,4) DEFAULT 0
service_amount NUMERIC(20,4) DEFAULT 0
tax_amount NUMERIC(20,4) DEFAULT 0
total_amount NUMERIC(20,4)
payment_status VARCHAR(20)
sap_ap_invoice_doc_entry INTEGER NULL
sap_payment_doc_entry INTEGER NULL
```

Constraint:

```sql
UNIQUE (lease_contract_id, period_start, period_end);
CHECK (period_end >= period_start);
CHECK (total_amount >= 0);
```

---

## 14. Software dan lisensi

### 14.1 `software_products`

```text
software_products
-----------------
id UUID PK
product_code VARCHAR(50) UNIQUE
product_name VARCHAR(150)
publisher_partner_id UUID FK NULL
publisher_name VARCHAR(150) NULL
product_type VARCHAR(30)
version VARCHAR(50) NULL
edition VARCHAR(100) NULL
is_active BOOLEAN
```

### 14.2 `software_licenses`

```text
software_licenses
-----------------
id UUID PK
software_product_id UUID FK
license_number VARCHAR(150) NULL
license_key_encrypted TEXT NULL
license_model VARCHAR(30)
license_metric VARCHAR(30)
license_quantity INTEGER
used_quantity INTEGER DEFAULT 0
purchase_date DATE NULL
activation_date DATE NULL
start_date DATE NULL
expiry_date DATE NULL
renewal_type VARCHAR(30)
auto_renewal BOOLEAN
renewal_notice_days INTEGER DEFAULT 30
subscription_cost NUMERIC(20,4) NULL
currency_code CHAR(3) NULL
supplier_id UUID FK NULL
maintenance_contract_id UUID FK NULL
support_end_date DATE NULL
update_entitlement_end_date DATE NULL
status VARCHAR(20)
```

Nilai `license_model`:

```text
PERPETUAL
SUBSCRIPTION
TRIAL
OEM
OPEN_SOURCE
ENTERPRISE_AGREEMENT
CONCURRENT
NAMED_USER
DEVICE_BASED
CPU_CORE_BASED
```

Constraint:

```sql
CHECK (license_quantity >= 0);
CHECK (used_quantity >= 0);
CHECK (used_quantity <= license_quantity);
CHECK (expiry_date IS NULL OR start_date IS NULL OR expiry_date >= start_date);
```

`license_key_encrypted` tidak boleh dikembalikan oleh endpoint list biasa, tidak boleh masuk log, dan hanya boleh didekripsi melalui service khusus dengan authorization serta audit.

### 14.3 `software_installations`

```text
software_installations
----------------------
id UUID PK
software_license_id UUID FK
installed_on_asset_id UUID FK
installation_date DATE
installed_version VARCHAR(50)
installation_path TEXT NULL
license_seat_number VARCHAR(50) NULL
last_update_date DATE NULL
current_patch_level VARCHAR(100) NULL
installation_status VARCHAR(20)
uninstalled_at TIMESTAMPTZ NULL
```

### 14.4 `software_license_assignments`

Mendukung assignment lisensi ke perangkat atau named user.

```text
software_license_assignments
----------------------------
id UUID PK
software_license_id UUID FK
asset_id UUID FK NULL
employee_id UUID FK NULL
assignment_type VARCHAR(30)
assigned_at TIMESTAMPTZ
released_at TIMESTAMPTZ NULL
```

Constraint:

```sql
CHECK (
    (asset_id IS NOT NULL AND employee_id IS NULL)
 OR (asset_id IS NULL AND employee_id IS NOT NULL)
);
```

`used_quantity` sebaiknya merupakan nilai turunan dari assignment/installation aktif atau diperbarui secara atomik dalam service. Jangan mengandalkan input langsung pengguna.

---

## 15. Maintenance contract dan SLA

### 15.1 `service_levels`

```text
service_levels
--------------
id UUID PK
sla_code VARCHAR(30) UNIQUE
sla_name VARCHAR(100)
priority_level VARCHAR(20)
response_time_hours NUMERIC(8,2)
resolution_time_hours NUMERIC(8,2)
availability_target_percent NUMERIC(8,4) NULL
penalty_rule TEXT NULL
```

### 15.2 `maintenance_contracts`

```text
maintenance_contracts
---------------------
id UUID PK
contract_number VARCHAR(100) UNIQUE
contract_name VARCHAR(200)
vendor_partner_id UUID FK
contract_type VARCHAR(30)
start_date DATE
end_date DATE
service_level_id UUID FK NULL
response_time_hours NUMERIC(8,2) NULL
resolution_time_hours NUMERIC(8,2) NULL
preventive_maintenance_included BOOLEAN
corrective_maintenance_included BOOLEAN
spare_parts_included BOOLEAN
labor_included BOOLEAN
onsite_support_included BOOLEAN
remote_support_included BOOLEAN
contract_value NUMERIC(20,4)
currency_code CHAR(3)
billing_frequency VARCHAR(20)
auto_renewal BOOLEAN
notice_period_days INTEGER NULL
status VARCHAR(20)
sap_purchase_contract_reference VARCHAR(100) NULL
```

Nilai `contract_type`:

```text
AMC
FULL_SERVICE
PREVENTIVE_ONLY
CORRECTIVE_ONLY
SUPPORT
CALIBRATION
INSPECTION
SOFTWARE_SUPPORT
```

### 15.3 `maintenance_contract_assets`

```text
maintenance_contract_assets
---------------------------
id UUID PK
maintenance_contract_id UUID FK
asset_id UUID FK
coverage_start_date DATE
coverage_end_date DATE
coverage_level VARCHAR(30)
annual_allocation_amount NUMERIC(20,4) NULL
specific_exclusions TEXT NULL
```

Constraint:

```sql
UNIQUE (maintenance_contract_id, asset_id, coverage_start_date);
CHECK (coverage_end_date >= coverage_start_date);
```

Periode coverage harus berada di dalam periode kontrak.

Warranty dan maintenance contract harus tetap dipisahkan. Warranty merupakan hak dari pembelian atau produsen, sedangkan maintenance contract adalah kontrak layanan yang umumnya berbayar dan memiliki SLA.

---

## 16. Lifetime, lifecycle, dan replacement

Lifetime yang harus dibedakan:

| Lifetime | Arti |
|---|---|
| Accounting useful life | Dasar depresiasi per depreciation area |
| Technical life | Kemampuan teknis aset untuk beroperasi |
| Economic life | Periode aset masih ekonomis digunakan |
| Contract life | Masa kontrak sewa atau layanan |
| Support life | Masa dukungan vendor |
| Warranty life | Masa garansi |

### 16.1 `asset_lifecycle_profiles`

Satu current profile untuk setiap aset.

```text
asset_lifecycle_profiles
------------------------
id UUID PK
asset_id UUID FK UNIQUE
technical_lifetime_months INTEGER NULL
economic_lifetime_months INTEGER NULL
accounting_useful_life_months INTEGER NULL
expected_replacement_date DATE NULL
support_end_date DATE NULL
vendor_end_of_sale_date DATE NULL
vendor_end_of_support_date DATE NULL
replacement_strategy VARCHAR(30)
replacement_priority VARCHAR(20)
estimated_replacement_cost NUMERIC(20,4) NULL
replacement_budget_year INTEGER NULL
next_review_date DATE NULL
```

Nilai `replacement_strategy`:

```text
RUN_TO_FAILURE
AGE_BASED
CONDITION_BASED
USAGE_BASED
TECHNOLOGY_REFRESH
CONTRACT_EXPIRY
REGULATORY_REQUIREMENT
```

### 16.2 `asset_lifecycle_reviews`

```text
asset_lifecycle_reviews
-----------------------
id UUID PK
asset_id UUID FK
review_date DATE
condition_score NUMERIC(5,2)
remaining_life_months INTEGER NULL
risk_score NUMERIC(5,2) NULL
replacement_recommendation VARCHAR(30)
estimated_replacement_cost NUMERIC(20,4) NULL
review_notes TEXT NULL
reviewed_by UUID
approved_by UUID NULL
```

Constraint:

```sql
UNIQUE (asset_id, review_date);
CHECK (condition_score BETWEEN 0 AND 100);
CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100);
```

---

## 17. Meter dan usage

### 17.1 `asset_meters`

```text
asset_meters
------------
id UUID PK
asset_id UUID FK
meter_type VARCHAR(30)
meter_name VARCHAR(100)
unit_of_measure VARCHAR(20)
initial_value NUMERIC(20,4)
current_value NUMERIC(20,4)
rollover_value NUMERIC(20,4) NULL
is_active BOOLEAN
```

### 17.2 `asset_meter_readings`

```text
asset_meter_readings
--------------------
id UUID PK
asset_meter_id UUID FK
reading_date TIMESTAMPTZ
reading_value NUMERIC(20,4)
source VARCHAR(30)
recorded_by UUID NULL
work_order_id UUID NULL
is_correction BOOLEAN DEFAULT FALSE
correction_reason TEXT NULL
```

Constraint:

```sql
UNIQUE (asset_meter_id, reading_date);
```

Nilai reading berikutnya tidak boleh lebih rendah dari nilai sebelumnya, kecuali:

- rollover;
- penggantian meter;
- koreksi yang disetujui.

`asset_meters.current_value` merupakan cache dan diperbarui atomik bersama insertion reading.

---

## 18. Document management

Satu file dapat terkait dengan banyak entitas. Gunakan dokumen generik dan tabel link.

### 18.1 `documents`

```text
documents
---------
id UUID PK
document_type VARCHAR(30)
document_number VARCHAR(100) NULL
document_name VARCHAR(200)
file_name VARCHAR(255)
storage_provider VARCHAR(30)
storage_key TEXT
mime_type VARCHAR(100)
file_size BIGINT
file_hash VARCHAR(128) NULL
issue_date DATE NULL
expiry_date DATE NULL
uploaded_at TIMESTAMPTZ
uploaded_by UUID
is_confidential BOOLEAN DEFAULT FALSE
```

### 18.2 `document_links`

```text
document_links
--------------
id UUID PK
document_id UUID FK
entity_type VARCHAR(50)
entity_id UUID
link_role VARCHAR(30) NULL
```

Constraint:

```sql
UNIQUE (document_id, entity_type, entity_id, link_role);
```

Karena foreign key polymorphic tidak dapat dijamin PostgreSQL secara langsung, service harus memvalidasi keberadaan `entity_id`. Alternatif yang lebih ketat adalah membuat link table khusus per entitas, tetapi menghasilkan lebih banyak tabel.

File tidak disimpan sebagai binary pada tabel bisnis. Database hanya menyimpan metadata dan storage key.

Nilai `document_type`:

```text
PURCHASE_INVOICE
WARRANTY_CERTIFICATE
LEASE_CONTRACT
MAINTENANCE_CONTRACT
LICENSE_CERTIFICATE
REGISTRATION_CERTIFICATE
INSURANCE_POLICY
MANUAL
TECHNICAL_DRAWING
PHOTO
HANDOVER_DOCUMENT
DISPOSAL_DOCUMENT
CALIBRATION_CERTIFICATE
```

---

## 19. Status history dan audit

### 19.1 `asset_status_histories`

```text
asset_status_histories
----------------------
id UUID PK
asset_id UUID FK
previous_status VARCHAR(30) NULL
new_status VARCHAR(30)
previous_condition VARCHAR(30) NULL
new_condition VARCHAR(30) NULL
effective_at TIMESTAMPTZ
reason TEXT NULL
reference_type VARCHAR(50) NULL
reference_id UUID NULL
changed_by UUID
```

### 19.2 `audit_logs`

```text
audit_logs
----------
id UUID PK
entity_type VARCHAR(50)
entity_id UUID
action VARCHAR(30)
actor_id UUID NULL
request_id UUID NULL
ip_address INET NULL
user_agent TEXT NULL
before_data JSONB NULL
after_data JSONB NULL
occurred_at TIMESTAMPTZ
```

Audit log bersifat append-only. Data rahasia seperti password, token, dan license key harus dihapus atau disamarkan sebelum data masuk audit.

---

## 20. Integrasi SAP Business One

### 20.1 Prinsip integrasi

1. Nama domain lokal tidak mengikuti langsung nama tabel database SAP B1.
2. Semua link eksternal menggunakan mapping terpisah.
3. Jangan melakukan query dan write langsung ke tabel database SAP B1.
4. Gunakan interface integrasi yang didukung oleh instalasi SAP B1, misalnya Service Layer, DI API, Integration Framework, atau middleware yang telah disetujui.
5. Konfirmasi object, field, dan ketersediaan endpoint terhadap versi serta database engine SAP B1 yang digunakan.
6. Semua operasi write harus idempotent.
7. Error integrasi tidak boleh membuat transaksi lokal setengah selesai.

### 20.2 Mapping istilah

| AMS | SAP B1 | Catatan |
|---|---|---|
| `asset_code` | Asset Number / Item Code | Simpan key internal dan kode yang terlihat |
| `asset_name` | Item/Asset Description | Nama aset |
| `asset_class_id` | Asset Class | Klasifikasi finansial |
| `capitalization_date` | Capitalization Date | Tanggal pengakuan |
| `depreciation_area` | Depreciation Area | Book, tax, management |
| `depreciation_method` | Depreciation Type | Metode penyusutan |
| `useful_life_months` | Useful Life | Dapat berbeda per area |
| `acquisition_cost` | Acquisition and Production Cost | Nilai perolehan |
| `accumulated_depreciation` | Accumulated Depreciation | Diambil dari SAP B1 |
| `net_book_value` | Net Book Value | Diambil dari SAP B1 |
| `supplier_id` | Business Partner / CardCode | Vendor |
| `sap_doc_entry` | DocEntry | Key internal |
| `sap_doc_num` | DocNum | Nomor yang terlihat |
| `sap_trans_id` | TransId | Referensi jurnal |
| `warehouse_code` | WhsCode | Warehouse |
| `bin_location_code` | Bin Location Code | Bin |

### 20.3 `sap_integration_mappings`

```text
sap_integration_mappings
------------------------
id UUID PK
entity_type VARCHAR(50)
local_entity_id UUID
sap_company_db VARCHAR(100)
sap_object_type VARCHAR(30)
sap_doc_entry INTEGER NULL
sap_doc_num INTEGER NULL
sap_item_code VARCHAR(50) NULL
sap_asset_code VARCHAR(50) NULL
sap_card_code VARCHAR(50) NULL
external_key VARCHAR(150) NULL
sync_direction VARCHAR(20)
sync_status VARCHAR(20)
last_synced_at TIMESTAMPTZ NULL
local_updated_at TIMESTAMPTZ NULL
sap_updated_at TIMESTAMPTZ NULL
last_error TEXT NULL
version_token VARCHAR(200) NULL
```

Nilai `sync_direction`:

```text
SAP_TO_AMS
AMS_TO_SAP
BIDIRECTIONAL
REFERENCE_ONLY
```

Constraint dapat menggunakan partial unique index:

```sql
CREATE UNIQUE INDEX uq_sap_mapping_doc_entry
ON sap_integration_mappings (
    sap_company_db,
    sap_object_type,
    sap_doc_entry
)
WHERE sap_doc_entry IS NOT NULL;

CREATE UNIQUE INDEX uq_sap_mapping_asset_code
ON sap_integration_mappings (
    sap_company_db,
    sap_asset_code
)
WHERE sap_asset_code IS NOT NULL;
```

### 20.4 Outbox dan inbox

Untuk integrasi yang andal, tambahkan:

```text
integration_outbox
------------------
id UUID PK
event_type VARCHAR(100)
aggregate_type VARCHAR(50)
aggregate_id UUID
payload JSONB
idempotency_key VARCHAR(150) UNIQUE
status VARCHAR(20)
attempt_count INTEGER DEFAULT 0
available_at TIMESTAMPTZ
processed_at TIMESTAMPTZ NULL
last_error TEXT NULL
created_at TIMESTAMPTZ

integration_inbox
-----------------
id UUID PK
source_system VARCHAR(30)
external_event_id VARCHAR(150)
event_type VARCHAR(100)
payload_hash VARCHAR(128)
received_at TIMESTAMPTZ
processed_at TIMESTAMPTZ NULL
status VARCHAR(20)
last_error TEXT NULL
```

Constraint:

```sql
UNIQUE (source_system, external_event_id);
```

Outbox event ditulis dalam transaksi yang sama dengan perubahan data lokal. Worker integrasi memproses outbox di luar HTTP request utama dengan retry dan exponential backoff.

### 20.5 State sinkronisasi

```text
PENDING
PROCESSING
SYNCED
FAILED_RETRYABLE
FAILED_PERMANENT
CONFLICT
IGNORED
```

### 20.6 Rekonsiliasi

Job rekonsiliasi terjadwal minimal memeriksa:

- asset lokal tanpa mapping SAP;
- mapping yang object SAP-nya tidak ditemukan;
- perbedaan asset class;
- perbedaan capitalization date;
- perbedaan nilai kapitalisasi;
- snapshot depresiasi yang belum diperbarui;
- retirement request yang belum mendapat dokumen SAP;
- duplikasi `sap_asset_code`;
- error integrasi yang melewati retry threshold.

---

## 21. Constraint temporal PostgreSQL

Untuk mencegah periode aktif saling tumpang tindih, aktifkan extension:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

Contoh untuk primary custodian:

```sql
ALTER TABLE asset_assignments
ADD CONSTRAINT ex_asset_primary_assignment_period
EXCLUDE USING gist (
    asset_id WITH =,
    tstzrange(
        assigned_at,
        COALESCE(returned_at, 'infinity'::timestamptz),
        '[)'
    ) WITH &&
)
WHERE (assignment_type = 'PRIMARY_CUSTODIAN');
```

Contoh untuk depreciation parameter:

```sql
ALTER TABLE asset_depreciation_parameters
ADD CONSTRAINT ex_asset_depreciation_period
EXCLUDE USING gist (
    asset_id WITH =,
    depreciation_area_id WITH =,
    daterange(
        valid_from,
        COALESCE(valid_to, 'infinity'::date),
        '[]'
    ) WITH &&
);
```

Alembic migration harus menguji dukungan extension dan constraint pada environment target.

---

## 22. Struktur modular FastAPI

Struktur yang direkomendasikan:

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── exceptions.py
│   ├── logging.py
│   └── middleware.py
├── shared/
│   ├── enums.py
│   ├── pagination.py
│   ├── responses.py
│   ├── filters.py
│   └── types.py
├── modules/
│   ├── organizations/
│   ├── partners/
│   ├── assets/
│   ├── locations/
│   ├── assignments/
│   ├── acquisitions/
│   ├── depreciation/
│   ├── warranties/
│   ├── leases/
│   ├── software_licenses/
│   ├── maintenance_contracts/
│   ├── lifecycle/
│   ├── meters/
│   ├── documents/
│   ├── sap_integration/
│   ├── notifications/
│   └── audit/
├── workers/
│   ├── sap_sync_worker.py
│   ├── notification_worker.py
│   └── reconciliation_worker.py
└── tests/
```

Struktur internal setiap module:

```text
assets/
├── router.py
├── schemas.py
├── models.py
├── repository.py
├── service.py
├── policies.py
├── exceptions.py
└── dependencies.py
```

Tanggung jawab layer:

| Layer | Tanggung jawab |
|---|---|
| Router | HTTP, dependency injection, status code, request/response |
| Schema | Validasi input-output Pydantic |
| Service | Use case, transaksi, rule lintas repository |
| Repository | Query persistence dan locking |
| Model | Mapping SQLAlchemy |
| Policy | Authorization dan business permission |
| Worker | Proses async, integrasi, retry, rekonsiliasi |

Router tidak boleh mengandung query SQLAlchemy atau logika bisnis yang kompleks.

---

## 23. Pola SQLAlchemy dan transaksi

### 23.1 Async database session

Gunakan satu session per request atau satu unit of work per worker job.

```python
async with session.begin():
    asset = await asset_repository.get_for_update(asset_id)
    await transfer_service.apply_transfer(asset, command)
```

### 23.2 Optimistic concurrency

`assets.version_no` bertambah setiap perubahan penting:

```sql
UPDATE assets
SET
    asset_status = :new_status,
    version_no = version_no + 1,
    updated_at = now()
WHERE id = :asset_id
  AND version_no = :expected_version;
```

Jika row count nol, kembalikan HTTP `409 Conflict`.

### 23.3 Database transaction boundary

Use case berikut wajib atomic:

- register asset dan ownership awal;
- approve transfer dan update current location;
- assign atau return asset;
- activate lease item;
- allocate dan release software license;
- update meter reading dan current meter;
- request retirement dan outbox event;
- sinkronisasi snapshot dan update mapping.

---

## 24. Desain API awal

Base path:

```text
/api/v1
```

### 24.1 Asset Registry

```text
POST   /assets
GET    /assets
GET    /assets/{asset_id}
PATCH  /assets/{asset_id}
GET    /assets/{asset_id}/timeline
GET    /assets/{asset_id}/financial-summary
POST   /assets/{asset_id}/status-changes
POST   /assets/{asset_id}/components
```

### 24.2 Location dan assignment

```text
POST   /asset-transfers
POST   /asset-transfers/{transfer_id}/submit
POST   /asset-transfers/{transfer_id}/approve
POST   /asset-transfers/{transfer_id}/complete
POST   /assets/{asset_id}/assignments
POST   /assignments/{assignment_id}/return
GET    /assets/{asset_id}/location-history
GET    /assets/{asset_id}/assignment-history
```

### 24.3 Contract dan entitlement

```text
POST   /warranties
POST   /warranties/{warranty_id}/claims
POST   /maintenance-contracts
POST   /maintenance-contracts/{contract_id}/assets
POST   /lease-contracts
POST   /lease-contracts/{contract_id}/assets
POST   /software-licenses
POST   /software-licenses/{license_id}/assignments
POST   /software-license-assignments/{assignment_id}/release
```

### 24.4 Lifecycle dan SAP

```text
POST   /assets/{asset_id}/lifecycle-reviews
POST   /assets/{asset_id}/retirement-requests
GET    /sap-integration/mappings
POST   /sap-integration/reconciliation
GET    /sap-integration/errors
POST   /sap-integration/errors/{error_id}/retry
```

Command endpoint dipilih untuk perubahan status yang memiliki business rule. Jangan menggunakan `PATCH` generik untuk approve, return, disposal, atau aktivitas workflow.

---

## 25. Format response dan error

Contoh response sukses:

```json
{
  "success": true,
  "data": {
    "id": "0198...",
    "asset_code": "AST-IT-0001",
    "asset_status": "IN_SERVICE",
    "version_no": 3
  },
  "meta": {
    "request_id": "0198..."
  }
}
```

Contoh error:

```json
{
  "success": false,
  "error": {
    "code": "ASSET_ASSIGNMENT_OVERLAP",
    "message": "Aset telah memiliki primary custodian aktif.",
    "details": {
      "asset_id": "0198...",
      "active_assignment_id": "0198..."
    }
  },
  "meta": {
    "request_id": "0198..."
  }
}
```

Status code:

| Kondisi | HTTP |
|---|---:|
| Data berhasil dibuat | 201 |
| Command diterima untuk proses async | 202 |
| Request berhasil | 200 |
| Validasi input | 422 |
| Tidak ditemukan | 404 |
| Konflik versi atau business state | 409 |
| Tidak terautentikasi | 401 |
| Tidak berwenang | 403 |
| Dependency SAP B1 gagal sementara | 503 |

---

## 26. Security dan authorization

Role awal:

```text
ASSET_ADMIN
ASSET_REGISTRAR
ASSET_CUSTODIAN
MAINTENANCE_OFFICER
LICENSE_ADMIN
FINANCE_VIEWER
SAP_INTEGRATION_OPERATOR
AUDITOR
APPROVER
```

Authorization harus mempertimbangkan:

- company;
- branch;
- department;
- asset category;
- command/action;
- nilai transaksi;
- status workflow.

Data sensitif:

- license key dienkripsi at rest;
- credential SAP B1 tidak disimpan pada source code;
- document confidential menggunakan access policy;
- endpoint audit hanya untuk auditor/admin;
- token, password, secret, dan license key tidak boleh dicatat di log.

Konfigurasi disediakan melalui environment variables atau secret manager:

```text
DATABASE_URL
APP_SECRET_KEY
ENCRYPTION_KEY
SAP_BASE_URL
SAP_COMPANY_DB
SAP_USERNAME
SAP_PASSWORD
SAP_VERIFY_SSL
DOCUMENT_STORAGE_PROVIDER
DOCUMENT_STORAGE_BUCKET
```

---

## 27. Notification dan scheduled job

Event yang perlu menghasilkan notifikasi:

- warranty akan berakhir;
- lease akan berakhir;
- contract renewal notice;
- software license expiry;
- software license capacity penuh;
- update entitlement berakhir;
- vendor support berakhir;
- lifecycle review jatuh tempo;
- replacement date mendekat;
- asset belum dikembalikan;
- maintenance contract coverage berakhir;
- SAP sync gagal;
- reconciliation mismatch.

Notifikasi tidak disimpan hanya sebagai boolean pada entitas. Gunakan:

```text
notification_rules
notification_events
notification_deliveries
```

Job harus idempotent agar satu event tidak mengirim notifikasi berulang untuk channel dan penerima yang sama.

---

## 28. Index strategy

Index minimum:

```sql
CREATE INDEX ix_assets_status
    ON assets (company_id, asset_status);

CREATE INDEX ix_assets_location
    ON assets (current_location_id)
    WHERE current_location_id IS NOT NULL;

CREATE INDEX ix_assets_serial_number
    ON assets (serial_number)
    WHERE serial_number IS NOT NULL;

CREATE INDEX ix_assignment_active
    ON asset_assignments (asset_id, assignment_type)
    WHERE returned_at IS NULL;

CREATE INDEX ix_warranty_expiry_active
    ON asset_warranties (end_date)
    WHERE status IN ('ACTIVE', 'EXPIRING');

CREATE INDEX ix_license_expiry_active
    ON software_licenses (expiry_date)
    WHERE status = 'ACTIVE';

CREATE INDEX ix_contract_expiry_active
    ON maintenance_contracts (end_date)
    WHERE status = 'ACTIVE';

CREATE INDEX ix_outbox_pending
    ON integration_outbox (available_at, created_at)
    WHERE status IN ('PENDING', 'FAILED_RETRYABLE');
```

Hindari index pada setiap kolom. Tambahkan index berdasarkan query, filter, join, dan laporan nyata.

---

## 29. Testing strategy

### 29.1 Unit test

Wajib mencakup:

- validasi perubahan status;
- perhitungan seat license;
- periode contract dan coverage;
- periode lease item;
- aturan claim warranty;
- current state dari history;
- masking/encryption license key;
- pembentukan idempotency key.

### 29.2 Integration test database

- FK dan delete rule;
- unique dan partial unique index;
- exclusion constraint periode;
- transaction rollback;
- optimistic concurrency;
- `SELECT FOR UPDATE`;
- outbox ditulis atomik.

Gunakan PostgreSQL untuk test integrasi. SQLite tidak cukup untuk menguji `JSONB`, exclusion constraint, range type, partial index, dan locking PostgreSQL.

### 29.3 Contract test SAP B1

- authentication/session;
- mapping request-response;
- pagination;
- timeout dan retry;
- duplicate request;
- unauthorized/expired session;
- object tidak ditemukan;
- perubahan data di kedua sistem;
- rate limiting jika ada;
- versi SAP B1 yang digunakan.

### 29.4 End-to-end scenario

Skenario minimum:

1. register asset pembelian;
2. sinkronkan nilai kapitalisasi dari SAP B1;
3. assign kepada employee;
4. pindahkan lokasi dan custodian;
5. tambahkan warranty dan claim;
6. hubungkan maintenance contract;
7. pasang software license;
8. buat lifecycle review;
9. request retirement;
10. konfirmasi retirement dari SAP B1.

---

## 30. Tahapan implementasi

### Phase 0 — Validasi integrasi

- tetapkan versi dan database engine SAP B1;
- inventaris object serta field yang tersedia;
- tetapkan interface integrasi;
- validasi autentikasi dan session management;
- sepakati system of record per data;
- definisikan company, branch, warehouse, dan BP mapping.

### Phase 1 — Asset Registry MVP

Tabel:

```text
asset_categories
asset_classes
assets
asset_attribute_definitions
asset_attribute_values
business_partners
business_partner_roles
asset_ownerships
asset_locations
asset_location_histories
asset_assignments
asset_status_histories
documents
document_links
audit_logs
sap_integration_mappings
```

Fitur:

- register dan search asset;
- hierarchy asset;
- QR/barcode;
- lokasi;
- assignment;
- timeline;
- dokumen;
- mapping dasar SAP B1.

### Phase 2 — Financial reference dan contract

Tabel:

```text
asset_acquisitions
depreciation_areas
depreciation_methods
asset_depreciation_parameters
asset_value_snapshots
asset_warranties
asset_warranty_claims
maintenance_contracts
maintenance_contract_assets
service_levels
asset_lease_contracts
asset_lease_items
asset_lease_payments
```

### Phase 3 — Software dan lifecycle

Tabel:

```text
software_products
software_licenses
software_installations
software_license_assignments
asset_lifecycle_profiles
asset_lifecycle_reviews
asset_meters
asset_meter_readings
```

### Phase 4 — Integration hardening

- outbox/inbox;
- worker retry;
- reconciliation;
- conflict handling;
- monitoring dan alert;
- performance test;
- archival dan retention.

### Phase 5 — Maintenance operations

Tahap lanjutan:

- work order;
- preventive maintenance schedule;
- corrective maintenance;
- inspection;
- calibration;
- spare part;
- downtime;
- maintenance cost;
- failure analysis.

---

## 31. Keputusan arsitektur yang harus dipertahankan

1. `assets` bukan tempat seluruh atribut dan histori.
2. Category operasional dan Asset Class finansial merupakan master berbeda.
3. Satu aset dapat memiliki banyak acquisition/capitalization event.
4. Depresiasi disimpan per asset dan depreciation area.
5. Nilai buku dari SAP B1 disimpan sebagai snapshot, bukan dihitung ulang menjadi sumber kebenaran lokal.
6. Warranty dan maintenance contract merupakan domain berbeda.
7. Lease contract dan maintenance contract berelasi many-to-many dengan aset.
8. Software license tidak menjadi kolom pada komputer/server.
9. Software license berelasi ke asset/user melalui installation atau assignment.
10. Useful life, technical life, support expiry, contract expiry, dan warranty expiry tidak boleh disatukan.
11. Perubahan lokasi, pemegang, status, kondisi, dan lifecycle harus memiliki histori.
12. Integrasi SAP B1 menggunakan mapping, idempotency, outbox/inbox, dan rekonsiliasi.
13. Write langsung ke tabel database SAP B1 tidak diperbolehkan.
14. Workflow penting menggunakan command endpoint, bukan patch status generik.
15. Constraint utama ditempatkan di database dan diperkuat oleh service layer.

---

## 32. Open decisions sebelum coding

Keputusan berikut harus ditetapkan bersama tim bisnis, SAP B1, dan development:

| Keputusan | Dampak |
|---|---|
| Versi dan database engine SAP B1 | Object, endpoint, dan cara integrasi |
| Service Layer, DI API, B1iF, atau middleware | Arsitektur deployment dan session |
| Single company atau multi-company | Scope unique key dan authorization |
| Sumber master employee | Assignment dan user mapping |
| Sumber master location | Warehouse/bin vs lokasi operasional |
| Aturan asset code | Import, numbering, QR/barcode |
| Kriteria aset finansial vs non-finansial | Kewajiban mapping ke Fixed Assets |
| Workflow approval | Status dan role |
| Storage document | Security, retention, dan backup |
| Notification channel | Email, aplikasi, atau messaging |
| Retention audit | Kapasitas database dan compliance |
| Mata uang dan fiscal period | Snapshot dan reporting |

---

## 33. Definition of Done untuk model data

Model dianggap siap memasuki pengembangan ketika:

- seluruh tabel memiliki PK, FK, unique constraint, dan delete rule;
- seluruh enum/domain status telah disepakati;
- system of record per field penting terdokumentasi;
- overlap temporal telah ditangani;
- transaction boundary telah ditentukan;
- object mapping SAP B1 telah diverifikasi pada environment target;
- migration dapat dijalankan dari database kosong;
- migration downgrade yang aman tersedia untuk perubahan non-destruktif;
- integration tests berjalan pada PostgreSQL;
- sample dataset mencakup aset milik sendiri, sewa, mitra, software, warranty, dan maintenance contract;
- API contract untuk MVP telah disetujui;
- audit dan authorization telah diuji.

---

## 34. Kesimpulan

Pusat data tetap berada pada:

```text
assets
```

Namun `assets` hanya menyimpan identitas dan keadaan terkini. Data finansial, kontraktual, teknis, penggunaan, serta lifecycle ditempatkan pada tabel terpisah dengan relasi dan histori yang jelas.

Arsitektur ini membuat SAP Business One tetap menjadi sumber kebenaran finansial, sementara aplikasi FastAPI menjadi lapisan operasional yang menangani lifecycle aset secara lebih lengkap. Pemisahan tersebut mengurangi duplikasi fungsi SAP B1, menjaga auditability, dan memungkinkan pengembangan bertahap mulai dari Asset Registry MVP hingga maintenance operations yang penuh.

---

# 35. Maintenance Operations

## 35.1 Tujuan dan batas domain

Domain Maintenance Operations menangani:

- permintaan pemeliharaan manual;
- laporan gangguan, failure, kerusakan, dan penurunan performa;
- preventive, corrective, predictive, inspection, calibration, dan emergency maintenance;
- jadwal manual maupun jadwal yang dihasilkan dari request atau rencana rutin;
- tim pemeliharaan yang terdiri atas karyawan;
- pelaksanaan oleh tim internal, partner/vendor, atau kombinasi keduanya;
- keterkaitan dengan kontrak pemeliharaan, warranty, dan SLA;
- checklist inspeksi dan temuan lanjutan;
- kebutuhan, reservasi, pemakaian, serta penggantian spare part;
- downtime, biaya, bukti pekerjaan, dan riwayat pemeliharaan aset.

Empat objek bisnis berikut harus dipisahkan:

| Objek | Fungsi |
|---|---|
| `maintenance_requests` | Mencatat kebutuhan, keluhan, atau laporan gangguan |
| `maintenance_work_orders` | Memberikan otorisasi dan instruksi pekerjaan |
| `maintenance_schedules` | Menetapkan kapan pekerjaan direncanakan |
| `maintenance_work_order_events` | Menyimpan histori perubahan dan aktivitas |

Satu request tidak selalu langsung menjadi pekerjaan. Request harus melalui triage, verifikasi cakupan kontrak/warranty, penetapan prioritas, serta penugasan.

## 35.2 Alur proses utama

```mermaid
flowchart TD
    A["Request / checklist / rencana rutin"] --> B["Triage dan klasifikasi"]
    B --> C{"Perlu tindakan?"}
    C -- Tidak --> D["Tolak atau tutup dengan alasan"]
    C -- Ya --> E["Work order"]
    E --> F["Jadwal dan tim/vendor"]
    F --> G["Pelaksanaan dan checklist"]
    G --> H{"Ada temuan lanjutan?"}
    H -- Ya --> I["Request turunan"]
    H -- Tidak --> J["Verifikasi hasil"]
    I --> B
    J --> K["Close dan maintenance history"]
```

Sumber pembentukan request:

```text
MANUAL
ASSET_USER
TECHNICIAN
CHECKLIST_FINDING
PREVENTIVE_SCHEDULE
METER_THRESHOLD
CONDITION_MONITORING
SYSTEM_ALERT
VENDOR_RECOMMENDATION
```

Sumber pembentukan work order:

```text
MAINTENANCE_REQUEST
PREVENTIVE_PLAN
MANUAL_PLANNING
CHECKLIST_FOLLOW_UP
WARRANTY_CLAIM
CONTRACT_SERVICE_VISIT
```

## 35.3 Master prioritas

Prioritas tidak cukup disimpan sebagai teks `urgent`. Gunakan master agar aturan SLA, target respons, eskalasi, dan warna tampilan dapat dikonfigurasi.

```sql
maintenance_priorities
----------------------
id UUID PK
code VARCHAR(30) UNIQUE NOT NULL
name VARCHAR(100) NOT NULL
severity_level SMALLINT NOT NULL
default_response_minutes INTEGER NULL
default_resolution_minutes INTEGER NULL
escalation_after_minutes INTEGER NULL
color_code VARCHAR(20) NULL
is_emergency BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
```

Nilai awal:

| Code | Makna |
|---|---|
| `LOW` | Tidak berdampak langsung pada operasi |
| `NORMAL` | Gangguan terbatas dan masih dapat ditoleransi |
| `HIGH` | Mengganggu operasi atau berisiko membesar |
| `URGENT` | Memerlukan tindakan segera |
| `EMERGENCY` | Risiko keselamatan, lingkungan, atau penghentian operasi kritis |

Prioritas harus ditentukan dari kombinasi:

- dampak operasional;
- urgensi waktu;
- criticality aset;
- aspek keselamatan;
- dampak lingkungan;
- potensi kehilangan produksi;
- availability redundansi;
- SLA kontrak.

Perubahan prioritas setelah triage harus menyimpan alasan dan pengguna yang mengubahnya.

## 35.4 Request pemeliharaan dan laporan gangguan

### `maintenance_requests`

```sql
maintenance_requests
--------------------
id UUID PK
request_number VARCHAR(50) UNIQUE NOT NULL
company_id UUID FK NOT NULL
asset_id UUID FK NOT NULL
parent_request_id UUID FK NULL

request_type VARCHAR(30) NOT NULL
source_type VARCHAR(30) NOT NULL
requested_by_employee_id UUID FK NULL
reported_by_name VARCHAR(150) NULL
reported_at TIMESTAMPTZ NOT NULL

title VARCHAR(200) NOT NULL
problem_description TEXT NOT NULL
symptom_code_id UUID FK NULL
failure_mode_id UUID FK NULL
priority_id UUID FK NOT NULL

asset_location_id UUID FK NULL
operating_condition TEXT NULL
meter_reading_id UUID FK NULL

is_asset_stopped BOOLEAN DEFAULT FALSE
downtime_started_at TIMESTAMPTZ NULL
safety_impact BOOLEAN DEFAULT FALSE
environmental_impact BOOLEAN DEFAULT FALSE
production_impact BOOLEAN DEFAULT FALSE

maintenance_contract_id UUID FK NULL
warranty_id UUID FK NULL
requested_vendor_partner_id UUID FK NULL

status VARCHAR(30) NOT NULL
triaged_by_employee_id UUID FK NULL
triaged_at TIMESTAMPTZ NULL
rejection_reason TEXT NULL
cancellation_reason TEXT NULL

required_response_at TIMESTAMPTZ NULL
required_resolution_at TIMESTAMPTZ NULL
created_at TIMESTAMPTZ NOT NULL
created_by UUID NOT NULL
updated_at TIMESTAMPTZ NOT NULL
version INTEGER NOT NULL DEFAULT 1
```

`request_type`:

```text
CORRECTIVE
BREAKDOWN
EMERGENCY
INSPECTION_FOLLOW_UP
PART_REPLACEMENT
PERFORMANCE_DEGRADATION
SAFETY
CALIBRATION
OTHER
```

Status request:

```text
DRAFT
SUBMITTED
TRIAGE
WAITING_INFORMATION
APPROVED
REJECTED
CONVERTED_TO_WORK_ORDER
IN_PROGRESS
RESOLVED
CLOSED
CANCELLED
```

Aturan:

- satu request harus menunjuk satu aset utama;
- subasset atau komponen terdampak dapat ditambahkan pada tabel detail;
- `parent_request_id` digunakan untuk request lanjutan dari checklist atau pekerjaan sebelumnya;
- request tidak boleh menjadi satu-satunya penyimpan informasi failure;
- satu request dapat menghasilkan lebih dari satu work order;
- satu work order dapat menggabungkan beberapa request yang berhubungan.

### `maintenance_request_assets`

Digunakan bila gangguan pada satu kejadian memengaruhi beberapa aset atau komponen.

```sql
maintenance_request_assets
--------------------------
id UUID PK
maintenance_request_id UUID FK NOT NULL
asset_id UUID FK NOT NULL
impact_type VARCHAR(30) NOT NULL
notes TEXT NULL

UNIQUE (maintenance_request_id, asset_id)
```

### `asset_failures`

```sql
asset_failures
--------------
id UUID PK
failure_number VARCHAR(50) UNIQUE NOT NULL
asset_id UUID FK NOT NULL
maintenance_request_id UUID FK NULL
work_order_id UUID FK NULL

detected_at TIMESTAMPTZ NOT NULL
detected_by_employee_id UUID FK NULL
failure_mode_id UUID FK NULL
symptom_code_id UUID FK NULL

failure_description TEXT NOT NULL
failure_severity VARCHAR(20) NOT NULL
asset_condition_before VARCHAR(30) NULL
asset_condition_after VARCHAR(30) NULL

caused_shutdown BOOLEAN DEFAULT FALSE
safety_incident BOOLEAN DEFAULT FALSE
repeat_failure BOOLEAN DEFAULT FALSE

temporary_action TEXT NULL
root_cause_code_id UUID FK NULL
root_cause_description TEXT NULL
corrective_action TEXT NULL
preventive_action TEXT NULL

failure_started_at TIMESTAMPTZ NULL
failure_ended_at TIMESTAMPTZ NULL
downtime_minutes INTEGER NULL
status VARCHAR(30) NOT NULL
created_at TIMESTAMPTZ NOT NULL
created_by UUID NOT NULL
```

Master pendukung:

```text
maintenance_symptom_codes
maintenance_failure_modes
maintenance_root_cause_codes
```

Pemisahan ini memungkinkan analisis MTBF, repeated failure, penyebab dominan, dan efektivitas tindakan tanpa mengandalkan teks bebas.

## 35.5 Tim pemeliharaan

### `maintenance_teams`

```sql
maintenance_teams
-----------------
id UUID PK
company_id UUID FK NOT NULL
team_code VARCHAR(30) NOT NULL
team_name VARCHAR(150) NOT NULL
team_type VARCHAR(30) NOT NULL
department_id UUID FK NULL
supervisor_employee_id UUID FK NULL
default_location_id UUID FK NULL
is_active BOOLEAN DEFAULT TRUE

UNIQUE (company_id, team_code)
```

`team_type`:

```text
MECHANICAL
ELECTRICAL
INSTRUMENTATION
IT
FACILITY
VEHICLE
GENERAL
MIXED
```

### `maintenance_team_members`

```sql
maintenance_team_members
------------------------
id UUID PK
maintenance_team_id UUID FK NOT NULL
employee_id UUID FK NOT NULL
member_role VARCHAR(30) NOT NULL
skill_level VARCHAR(20) NULL
effective_from DATE NOT NULL
effective_to DATE NULL
is_primary BOOLEAN DEFAULT FALSE

UNIQUE (maintenance_team_id, employee_id, effective_from)
```

`member_role`:

```text
SUPERVISOR
PLANNER
LEAD_TECHNICIAN
TECHNICIAN
INSPECTOR
HELPER
```

Keanggotaan dibuat historis karena susunan tim dapat berubah. Karyawan tetap bersumber dari master `employees`; tidak boleh disalin menjadi teks pada tim.

### Kompetensi

```sql
maintenance_skills
------------------
id UUID PK
skill_code VARCHAR(30) UNIQUE NOT NULL
skill_name VARCHAR(150) NOT NULL
certification_required BOOLEAN DEFAULT FALSE

employee_maintenance_skills
---------------------------
id UUID PK
employee_id UUID FK NOT NULL
maintenance_skill_id UUID FK NOT NULL
proficiency_level VARCHAR(20) NULL
certificate_number VARCHAR(100) NULL
valid_from DATE NULL
valid_to DATE NULL

UNIQUE (employee_id, maintenance_skill_id, valid_from)
```

Work order dapat menetapkan skill wajib agar planner tidak menugaskan personel yang sertifikasinya kedaluwarsa.

## 35.6 Rencana dan jadwal pemeliharaan

Pisahkan pola berulang dari kejadian jadwal aktual.

### `maintenance_plans`

```sql
maintenance_plans
-----------------
id UUID PK
plan_code VARCHAR(50) UNIQUE NOT NULL
plan_name VARCHAR(200) NOT NULL
asset_id UUID FK NULL
asset_category_id UUID FK NULL
maintenance_type VARCHAR(30) NOT NULL

trigger_type VARCHAR(30) NOT NULL
calendar_interval_value INTEGER NULL
calendar_interval_unit VARCHAR(20) NULL
meter_id UUID FK NULL
meter_interval NUMERIC(20,4) NULL
condition_rule JSONB NULL

default_priority_id UUID FK NOT NULL
default_team_id UUID FK NULL
default_vendor_partner_id UUID FK NULL
maintenance_contract_id UUID FK NULL
checklist_template_id UUID FK NULL

estimated_duration_minutes INTEGER NULL
lead_time_days INTEGER DEFAULT 0
auto_create_request BOOLEAN DEFAULT FALSE
auto_create_work_order BOOLEAN DEFAULT TRUE
requires_approval BOOLEAN DEFAULT FALSE

effective_from DATE NOT NULL
effective_to DATE NULL
next_due_date DATE NULL
next_due_meter_value NUMERIC(20,4) NULL
is_active BOOLEAN DEFAULT TRUE
```

`trigger_type`:

```text
CALENDAR
METER
CALENDAR_OR_METER
CALENDAR_AND_METER
CONDITION
MANUAL
```

Satu plan dapat diterapkan langsung ke aset atau melalui kategori. Untuk skala besar, ekspansi category-to-asset sebaiknya disimpan pada:

```sql
maintenance_plan_assets
-----------------------
id UUID PK
maintenance_plan_id UUID FK NOT NULL
asset_id UUID FK NOT NULL
effective_from DATE NOT NULL
effective_to DATE NULL
override_interval_value INTEGER NULL
override_interval_unit VARCHAR(20) NULL
is_active BOOLEAN DEFAULT TRUE

UNIQUE (maintenance_plan_id, asset_id, effective_from)
```

### `maintenance_schedules`

```sql
maintenance_schedules
---------------------
id UUID PK
schedule_number VARCHAR(50) UNIQUE NOT NULL
maintenance_plan_id UUID FK NULL
maintenance_request_id UUID FK NULL
work_order_id UUID FK NULL
asset_id UUID FK NOT NULL

schedule_source VARCHAR(30) NOT NULL
scheduled_start_at TIMESTAMPTZ NOT NULL
scheduled_end_at TIMESTAMPTZ NOT NULL
maintenance_team_id UUID FK NULL
vendor_partner_id UUID FK NULL
maintenance_contract_id UUID FK NULL

status VARCHAR(30) NOT NULL
reschedule_count INTEGER DEFAULT 0
reschedule_reason TEXT NULL
confirmed_at TIMESTAMPTZ NULL
created_by UUID NOT NULL
created_at TIMESTAMPTZ NOT NULL
```

`schedule_source`:

```text
MANUAL
REQUEST
PREVENTIVE_PLAN
METER_TRIGGER
CONDITION_TRIGGER
VENDOR_VISIT
FOLLOW_UP
```

Status:

```text
PLANNED
CONFIRMED
DISPATCHED
IN_PROGRESS
COMPLETED
MISSED
POSTPONED
CANCELLED
```

Aturan jadwal:

- `scheduled_end_at > scheduled_start_at`;
- jadwal dari request tetap menyimpan `maintenance_request_id`;
- jadwal rutin menyimpan `maintenance_plan_id`;
- jadwal tidak menjadi histori pekerjaan; hasil tetap dicatat di work order;
- benturan jadwal tim, teknisi, aset, dan vendor divalidasi service layer;
- reschedule tidak menghapus record lama: simpan event perubahan dan alasan.

## 35.7 Work order pemeliharaan

### `maintenance_work_orders`

```sql
maintenance_work_orders
-----------------------
id UUID PK
work_order_number VARCHAR(50) UNIQUE NOT NULL
company_id UUID FK NOT NULL
asset_id UUID FK NOT NULL
maintenance_type VARCHAR(30) NOT NULL
priority_id UUID FK NOT NULL

title VARCHAR(200) NOT NULL
scope_of_work TEXT NOT NULL
maintenance_plan_id UUID FK NULL
maintenance_team_id UUID FK NULL
lead_technician_id UUID FK NULL

execution_mode VARCHAR(20) NOT NULL
vendor_partner_id UUID FK NULL
maintenance_contract_id UUID FK NULL
warranty_id UUID FK NULL

planned_start_at TIMESTAMPTZ NULL
planned_end_at TIMESTAMPTZ NULL
actual_start_at TIMESTAMPTZ NULL
actual_end_at TIMESTAMPTZ NULL

asset_condition_before VARCHAR(30) NULL
asset_condition_after VARCHAR(30) NULL
completion_summary TEXT NULL
resolution_code VARCHAR(30) NULL

requires_shutdown BOOLEAN DEFAULT FALSE
requires_permit BOOLEAN DEFAULT FALSE
requires_verification BOOLEAN DEFAULT TRUE

status VARCHAR(30) NOT NULL
approved_by UUID NULL
approved_at TIMESTAMPTZ NULL
verified_by_employee_id UUID FK NULL
verified_at TIMESTAMPTZ NULL
closed_by UUID NULL
closed_at TIMESTAMPTZ NULL

estimated_labor_cost NUMERIC(20,4) DEFAULT 0
estimated_part_cost NUMERIC(20,4) DEFAULT 0
estimated_vendor_cost NUMERIC(20,4) DEFAULT 0
actual_labor_cost NUMERIC(20,4) DEFAULT 0
actual_part_cost NUMERIC(20,4) DEFAULT 0
actual_vendor_cost NUMERIC(20,4) DEFAULT 0
currency_code VARCHAR(3) NULL

created_at TIMESTAMPTZ NOT NULL
created_by UUID NOT NULL
updated_at TIMESTAMPTZ NOT NULL
version INTEGER NOT NULL DEFAULT 1
```

`maintenance_type`:

```text
PREVENTIVE
CORRECTIVE
PREDICTIVE
CONDITION_BASED
BREAKDOWN
EMERGENCY
INSPECTION
CALIBRATION
OVERHAUL
IMPROVEMENT
```

`execution_mode`:

```text
INTERNAL
VENDOR
HYBRID
```

Status work order:

```text
DRAFT
WAITING_APPROVAL
APPROVED
PLANNED
ASSIGNED
IN_PROGRESS
ON_HOLD
WAITING_PART
WAITING_VENDOR
COMPLETED
VERIFICATION
CLOSED
CANCELLED
```

Transisi status harus melalui command endpoint. Contoh:

```text
POST /maintenance/work-orders/{id}/approve
POST /maintenance/work-orders/{id}/assign
POST /maintenance/work-orders/{id}/start
POST /maintenance/work-orders/{id}/hold
POST /maintenance/work-orders/{id}/resume
POST /maintenance/work-orders/{id}/complete
POST /maintenance/work-orders/{id}/verify
POST /maintenance/work-orders/{id}/close
POST /maintenance/work-orders/{id}/cancel
```

### Relasi request dan work order

Gunakan junction table agar mendukung banyak-ke-banyak.

```sql
maintenance_request_work_orders
-------------------------------
id UUID PK
maintenance_request_id UUID FK NOT NULL
work_order_id UUID FK NOT NULL
relationship_type VARCHAR(30) NOT NULL

UNIQUE (maintenance_request_id, work_order_id)
```

Contoh `relationship_type`:

```text
PRIMARY
COMBINED
FOLLOW_UP
DIAGNOSTIC
PART_REPLACEMENT
```

### Penugasan personel

```sql
maintenance_work_order_assignments
----------------------------------
id UUID PK
work_order_id UUID FK NOT NULL
employee_id UUID FK NOT NULL
assignment_role VARCHAR(30) NOT NULL
planned_minutes INTEGER NULL
actual_minutes INTEGER NULL
assigned_at TIMESTAMPTZ NOT NULL
accepted_at TIMESTAMPTZ NULL
released_at TIMESTAMPTZ NULL

UNIQUE (work_order_id, employee_id, assignment_role)
```

Tim berfungsi sebagai kelompok default. Assignment menyimpan personel yang benar-benar ditugaskan pada work order.

## 35.8 Checklist inspeksi dan temuan

### Template

```sql
maintenance_checklist_templates
-------------------------------
id UUID PK
template_code VARCHAR(50) UNIQUE NOT NULL
template_name VARCHAR(200) NOT NULL
asset_category_id UUID FK NULL
maintenance_type VARCHAR(30) NULL
version_number INTEGER NOT NULL
effective_from DATE NOT NULL
effective_to DATE NULL
is_active BOOLEAN DEFAULT TRUE

maintenance_checklist_template_items
------------------------------------
id UUID PK
checklist_template_id UUID FK NOT NULL
sequence_no INTEGER NOT NULL
item_code VARCHAR(50) NOT NULL
instruction TEXT NOT NULL
response_type VARCHAR(30) NOT NULL
is_required BOOLEAN DEFAULT TRUE
normal_min_value NUMERIC(20,4) NULL
normal_max_value NUMERIC(20,4) NULL
unit_of_measure VARCHAR(20) NULL
failure_response_rule VARCHAR(30) NULL

UNIQUE (checklist_template_id, sequence_no)
```

`response_type`:

```text
PASS_FAIL
YES_NO
NUMERIC
TEXT
PHOTO
MULTI_SELECT
METER_READING
```

### Eksekusi checklist

```sql
maintenance_checklist_executions
--------------------------------
id UUID PK
checklist_template_id UUID FK NOT NULL
work_order_id UUID FK NULL
maintenance_schedule_id UUID FK NULL
asset_id UUID FK NOT NULL
performed_by_employee_id UUID FK NOT NULL
started_at TIMESTAMPTZ NOT NULL
completed_at TIMESTAMPTZ NULL
overall_result VARCHAR(20) NULL
status VARCHAR(20) NOT NULL

maintenance_checklist_results
-----------------------------
id UUID PK
checklist_execution_id UUID FK NOT NULL
template_item_id UUID FK NOT NULL
result_status VARCHAR(20) NULL
boolean_value BOOLEAN NULL
numeric_value NUMERIC(20,4) NULL
text_value TEXT NULL
meter_reading_id UUID FK NULL
notes TEXT NULL
performed_at TIMESTAMPTZ NOT NULL

UNIQUE (checklist_execution_id, template_item_id)
```

### Temuan checklist

```sql
maintenance_findings
--------------------
id UUID PK
finding_number VARCHAR(50) UNIQUE NOT NULL
checklist_result_id UUID FK NULL
work_order_id UUID FK NULL
asset_id UUID FK NOT NULL
finding_type VARCHAR(30) NOT NULL
severity VARCHAR(20) NOT NULL
description TEXT NOT NULL
recommended_action TEXT NULL
requires_follow_up BOOLEAN DEFAULT FALSE
requires_asset_shutdown BOOLEAN DEFAULT FALSE
follow_up_due_date DATE NULL
generated_request_id UUID FK NULL
status VARCHAR(20) NOT NULL
reported_by_employee_id UUID FK NOT NULL
reported_at TIMESTAMPTZ NOT NULL
resolved_at TIMESTAMPTZ NULL
```

`finding_type`:

```text
FAILURE
DEFECT
ABNORMAL_CONDITION
SAFETY_RISK
PART_WEAR
PART_REPLACEMENT
FURTHER_INSPECTION
ADJUSTMENT
HOUSEKEEPING
DOCUMENTATION
```

Aturan penting:

- temuan tidak otomatis dianggap selesai ketika checklist selesai;
- temuan yang membutuhkan tindak lanjut dapat menghasilkan `maintenance_requests`;
- request turunan menyimpan sumber `CHECKLIST_FINDING`;
- `maintenance_findings.generated_request_id` dan `maintenance_requests.parent_request_id` mempertahankan traceability;
- hasil checklist tidak boleh diedit setelah work order ditutup; koreksi dibuat sebagai revision/audit event.

## 35.9 Spare part dan penggantian komponen

Referensi item dan transaksi persediaan tetap berada di SAP B1 jika SAP B1 menjadi system of record inventory. Aplikasi menyimpan kebutuhan operasional dan mapping transaksi.

```sql
maintenance_part_requirements
-----------------------------
id UUID PK
work_order_id UUID FK NOT NULL
part_item_id UUID FK NOT NULL
required_quantity NUMERIC(20,4) NOT NULL
reserved_quantity NUMERIC(20,4) DEFAULT 0
issued_quantity NUMERIC(20,4) DEFAULT 0
returned_quantity NUMERIC(20,4) DEFAULT 0
unit_of_measure VARCHAR(20) NOT NULL
requirement_status VARCHAR(20) NOT NULL
is_critical BOOLEAN DEFAULT FALSE
notes TEXT NULL

maintenance_part_usages
-----------------------
id UUID PK
work_order_id UUID FK NOT NULL
part_item_id UUID FK NOT NULL
asset_id UUID FK NOT NULL
quantity NUMERIC(20,4) NOT NULL
unit_cost NUMERIC(20,4) NULL
currency_code VARCHAR(3) NULL
usage_type VARCHAR(20) NOT NULL
used_at TIMESTAMPTZ NOT NULL
used_by_employee_id UUID FK NULL
sap_inventory_doc_entry INTEGER NULL
sap_inventory_doc_num INTEGER NULL
removed_component_asset_id UUID FK NULL
installed_component_asset_id UUID FK NULL
serial_number VARCHAR(100) NULL
```

`usage_type`:

```text
ISSUE
INSTALL
REPLACE
CONSUME
RETURN
SCRAP
```

Jika spare part merupakan aset/komponen berserial, penggantian harus memperbarui hierarchy `assets.parent_asset_id` secara transactional dan membuat histori komponen.

## 35.10 Vendor, kontrak, warranty, dan SLA

Request/work order dapat terkait:

```text
maintenance_contracts
maintenance_contract_assets
service_levels
asset_warranties
business_partners
```

Sebelum work order vendor disetujui, service harus memeriksa:

1. kontrak aktif pada tanggal request;
2. aset tercakup dalam `maintenance_contract_assets`;
3. tipe pekerjaan tercakup: preventive/corrective/parts/labor/onsite;
4. exclusion kontrak;
5. SLA yang berlaku berdasarkan prioritas;
6. warranty aktif dan cakupannya;
7. apakah biaya ditanggung, sebagian ditanggung, atau di luar kontrak.

Tambahkan snapshot SLA pada request agar perubahan master/kontrak tidak mengubah target historis:

```sql
maintenance_sla_snapshots
-------------------------
id UUID PK
maintenance_request_id UUID FK NOT NULL
maintenance_contract_id UUID FK NULL
service_level_id UUID FK NULL
priority_id UUID FK NOT NULL
response_target_minutes INTEGER NULL
resolution_target_minutes INTEGER NULL
response_due_at TIMESTAMPTZ NULL
resolution_due_at TIMESTAMPTZ NULL
responded_at TIMESTAMPTZ NULL
resolved_at TIMESTAMPTZ NULL
response_breached BOOLEAN DEFAULT FALSE
resolution_breached BOOLEAN DEFAULT FALSE
snapshot_payload JSONB NOT NULL
created_at TIMESTAMPTZ NOT NULL
```

Partner/vendor tidak menjadi anggota `maintenance_team_members` karena tabel tersebut khusus karyawan internal. Teknisi vendor dicatat pada:

```sql
maintenance_vendor_personnel
----------------------------
id UUID PK
work_order_id UUID FK NOT NULL
vendor_partner_id UUID FK NOT NULL
person_name VARCHAR(150) NOT NULL
contact_phone VARCHAR(50) NULL
technician_reference VARCHAR(100) NULL
check_in_at TIMESTAMPTZ NULL
check_out_at TIMESTAMPTZ NULL
```

## 35.11 Downtime dan waktu kerja

```sql
maintenance_downtimes
---------------------
id UUID PK
asset_id UUID FK NOT NULL
maintenance_request_id UUID FK NULL
work_order_id UUID FK NULL
downtime_type VARCHAR(30) NOT NULL
started_at TIMESTAMPTZ NOT NULL
ended_at TIMESTAMPTZ NULL
duration_minutes INTEGER NULL
production_loss_quantity NUMERIC(20,4) NULL
unit_of_measure VARCHAR(20) NULL
reason TEXT NOT NULL
```

Downtime tidak selalu sama dengan durasi work order. Mesin dapat berhenti sebelum request dibuat dan kembali beroperasi sebelum administrasi work order ditutup.

```sql
maintenance_labor_logs
----------------------
id UUID PK
work_order_id UUID FK NOT NULL
employee_id UUID FK NOT NULL
started_at TIMESTAMPTZ NOT NULL
ended_at TIMESTAMPTZ NULL
duration_minutes INTEGER NULL
activity_type VARCHAR(30) NOT NULL
hourly_rate NUMERIC(20,4) NULL
labor_cost NUMERIC(20,4) NULL
notes TEXT NULL
```

## 35.12 Riwayat pemeliharaan dan audit event

Riwayat pemeliharaan bukan tabel yang diisi ulang secara manual. Riwayat dibentuk dari work order yang telah selesai/ditutup dan seluruh event terkait.

```sql
maintenance_work_order_events
-----------------------------
id UUID PK
work_order_id UUID FK NOT NULL
event_type VARCHAR(40) NOT NULL
previous_status VARCHAR(30) NULL
new_status VARCHAR(30) NULL
event_at TIMESTAMPTZ NOT NULL
performed_by UUID NULL
employee_id UUID FK NULL
reason TEXT NULL
event_payload JSONB NULL
```

Contoh event:

```text
CREATED
APPROVED
ASSIGNED
SCHEDULED
RESCHEDULED
STARTED
PUT_ON_HOLD
PART_REQUESTED
PART_ISSUED
VENDOR_CALLED
CHECKLIST_COMPLETED
FAILURE_RECORDED
FINDING_CREATED
COMPLETED
VERIFIED
CLOSED
CANCELLED
```

Endpoint histori aset:

```text
GET /assets/{asset_id}/maintenance-history
```

Respons sebaiknya menggabungkan:

- work order dan jenis pemeliharaan;
- request dan gangguan asal;
- jadwal rencana versus aktual;
- tim, teknisi, dan vendor;
- checklist serta temuan;
- failure, root cause, dan tindakan;
- spare part yang digunakan/diganti;
- downtime dan labor time;
- biaya internal/vendor;
- dokumen, foto, dan sertifikat;
- meter sebelum/sesudah pekerjaan.

Untuk reporting yang berat, dapat dibuat materialized view:

```sql
asset_maintenance_history_view
```

Namun tabel transaksi tetap menjadi sumber kebenaran.

## 35.13 Relasi utama maintenance

```mermaid
erDiagram
    ASSETS ||--o{ MAINTENANCE_REQUESTS : reported_for
    MAINTENANCE_REQUESTS }o--o{ MAINTENANCE_WORK_ORDERS : converted_to
    MAINTENANCE_PLANS ||--o{ MAINTENANCE_SCHEDULES : generates
    MAINTENANCE_WORK_ORDERS ||--o{ MAINTENANCE_SCHEDULES : scheduled_as
    MAINTENANCE_TEAMS ||--o{ MAINTENANCE_TEAM_MEMBERS : consists_of
    MAINTENANCE_WORK_ORDERS ||--o{ MAINTENANCE_WORK_ORDER_ASSIGNMENTS : assigned_to
    MAINTENANCE_WORK_ORDERS ||--o{ MAINTENANCE_CHECKLIST_EXECUTIONS : executes
    MAINTENANCE_CHECKLIST_EXECUTIONS ||--o{ MAINTENANCE_CHECKLIST_RESULTS : contains
    MAINTENANCE_CHECKLIST_RESULTS ||--o{ MAINTENANCE_FINDINGS : produces
    MAINTENANCE_FINDINGS o|--o| MAINTENANCE_REQUESTS : creates_follow_up
    MAINTENANCE_WORK_ORDERS ||--o{ MAINTENANCE_PART_USAGES : consumes
    MAINTENANCE_WORK_ORDERS ||--o{ MAINTENANCE_WORK_ORDER_EVENTS : records
```

Relasi dengan kontrak:

```mermaid
erDiagram
    BUSINESS_PARTNERS ||--o{ MAINTENANCE_CONTRACTS : provides
    MAINTENANCE_CONTRACTS ||--o{ MAINTENANCE_CONTRACT_ASSETS : covers
    ASSETS ||--o{ MAINTENANCE_CONTRACT_ASSETS : covered_asset
    MAINTENANCE_CONTRACTS o|--o{ MAINTENANCE_REQUESTS : governs
    MAINTENANCE_CONTRACTS o|--o{ MAINTENANCE_WORK_ORDERS : governs
    SERVICE_LEVELS o|--o{ MAINTENANCE_CONTRACTS : defines
    MAINTENANCE_REQUESTS ||--o| MAINTENANCE_SLA_SNAPSHOTS : freezes
```

## 35.14 Constraint dan invariant penting

1. Work order `CLOSED` wajib memiliki `actual_start_at`, `actual_end_at`, `completion_summary`, dan verifier bila verifikasi diwajibkan.
2. `actual_end_at` tidak boleh lebih kecil dari `actual_start_at`.
3. Request berstatus `CONVERTED_TO_WORK_ORDER` wajib memiliki minimal satu junction ke work order.
4. Schedule harus menunjuk minimal salah satu dari plan, request, atau work order.
5. Work order vendor/hybrid wajib memiliki `vendor_partner_id`.
6. Kontrak yang dipilih harus aktif dan mencakup aset pada tanggal pekerjaan.
7. Checklist mandatory harus lengkap sebelum pekerjaan dapat diselesaikan.
8. Temuan kritis yang belum ditangani harus memblokir close atau memerlukan explicit risk acceptance.
9. Penggunaan part tidak boleh melebihi jumlah issue bersih tanpa transaksi tambahan.
10. Downtime terbuka hanya boleh satu per aset untuk kejadian yang sama.
11. Record transaksi yang telah closed tidak dihapus; koreksi menggunakan reversal, revision, atau event.
12. Nomor request, schedule, finding, failure, dan work order unik per company jika aplikasi multi-company.

Constraint PostgreSQL yang disarankan:

```sql
CHECK (scheduled_end_at > scheduled_start_at)
CHECK (actual_end_at IS NULL OR actual_start_at IS NOT NULL)
CHECK (actual_end_at IS NULL OR actual_end_at >= actual_start_at)
CHECK (effective_to IS NULL OR effective_to >= effective_from)
CHECK (required_quantity > 0)
CHECK (quantity > 0)
CHECK (duration_minutes IS NULL OR duration_minutes >= 0)
```

Temporal overlap untuk membership, plan assignment, dan coverage kontrak dapat menggunakan PostgreSQL exclusion constraint dengan `daterange`.

## 35.15 Transaction boundary

### Convert request menjadi work order

Dalam satu transaction:

1. lock request dengan optimistic/pessimistic control;
2. validasi status dan kelengkapan triage;
3. resolve kontrak, warranty, SLA, serta cakupan;
4. buat work order;
5. buat junction request–work order;
6. buat SLA snapshot bila relevan;
7. update status request;
8. tulis event dan audit log;
9. buat notifikasi/outbox.

### Selesaikan checklist dengan finding

Dalam satu transaction:

1. simpan seluruh hasil checklist;
2. hitung overall result;
3. buat finding untuk hasil abnormal;
4. bila rule mengharuskan, buat request turunan;
5. kaitkan `generated_request_id`;
6. update kondisi aset bila disetujui;
7. tulis event dan audit log.

### Close work order

Dalam satu transaction:

1. validasi checklist dan temuan wajib;
2. validasi transaksi part dan labor;
3. hitung biaya aktual dan downtime;
4. simpan meter reading akhir;
5. update failure/root cause;
6. update status/kondisi aset bila berubah;
7. hitung ulang next due pada maintenance plan;
8. tutup request yang telah resolved;
9. ubah work order menjadi `CLOSED`;
10. tulis event, audit log, dan integration outbox.

## 35.16 Struktur modul FastAPI

```text
app/modules/maintenance/
├── requests/
│   ├── routes.py
│   ├── schemas.py
│   ├── models.py
│   ├── repository.py
│   └── service.py
├── planning/
│   ├── routes.py
│   ├── schemas.py
│   ├── models.py
│   ├── scheduler.py
│   └── service.py
├── work_orders/
│   ├── routes.py
│   ├── schemas.py
│   ├── models.py
│   ├── repository.py
│   ├── state_machine.py
│   └── service.py
├── teams/
├── checklists/
├── failures/
├── parts/
├── contracts/
├── reporting/
└── shared/
    ├── enums.py
    ├── policies.py
    ├── exceptions.py
    └── events.py
```

Scheduler hanya menghasilkan due schedule/request/work order secara idempotent. Scheduler tidak mengeksekusi pekerjaan dan tidak boleh langsung menandai maintenance selesai.

Idempotency key preventive:

```text
maintenance_plan_id + asset_id + due_date/due_meter_value
```

## 35.17 Endpoint awal

```text
POST   /maintenance/requests
GET    /maintenance/requests
GET    /maintenance/requests/{id}
POST   /maintenance/requests/{id}/submit
POST   /maintenance/requests/{id}/triage
POST   /maintenance/requests/{id}/approve
POST   /maintenance/requests/{id}/reject
POST   /maintenance/requests/{id}/convert-to-work-order

POST   /maintenance/plans
GET    /maintenance/plans
POST   /maintenance/plans/{id}/generate
GET    /maintenance/schedules
POST   /maintenance/schedules
POST   /maintenance/schedules/{id}/reschedule

POST   /maintenance/work-orders
GET    /maintenance/work-orders
GET    /maintenance/work-orders/{id}
POST   /maintenance/work-orders/{id}/assign
POST   /maintenance/work-orders/{id}/start
POST   /maintenance/work-orders/{id}/complete
POST   /maintenance/work-orders/{id}/verify
POST   /maintenance/work-orders/{id}/close

POST   /maintenance/work-orders/{id}/checklists
POST   /maintenance/checklists/{id}/results
POST   /maintenance/findings/{id}/create-request
POST   /maintenance/work-orders/{id}/parts
POST   /maintenance/work-orders/{id}/labor-logs
POST   /maintenance/work-orders/{id}/failures

GET    /assets/{asset_id}/maintenance-history
GET    /maintenance/reports/backlog
GET    /maintenance/reports/sla
GET    /maintenance/reports/reliability
GET    /maintenance/reports/cost
```

## 35.18 Authorization

Role minimum:

```text
MAINTENANCE_REQUESTER
MAINTENANCE_PLANNER
MAINTENANCE_SUPERVISOR
MAINTENANCE_TECHNICIAN
MAINTENANCE_INSPECTOR
MAINTENANCE_MANAGER
CONTRACT_ADMIN
SPARE_PART_CONTROLLER
ASSET_MANAGER
AUDITOR
```

Contoh separation of duties:

- requester dapat membuat dan melihat request miliknya;
- planner membuat schedule dan assignment;
- supervisor melakukan triage dan approval operasional;
- technician mengisi aktivitas, checklist, part, dan hasil pekerjaan;
- inspector/verifier memverifikasi pekerjaan bila diwajibkan;
- contract admin menentukan kontrak dan coverage;
- auditor hanya membaca histori dan audit trail;
- teknisi tidak boleh memverifikasi pekerjaannya sendiri untuk aset kritis.

## 35.19 Integrasi SAP Business One

| Data | System of Record | Arah |
|---|---|---|
| Asset dan financial asset reference | SAP B1 / sesuai baseline | SAP B1 → AMS |
| Business Partner/vendor | SAP B1 | SAP B1 → AMS |
| Employee | SAP B1/HR master yang disepakati | → AMS |
| Item spare part dan warehouse | SAP B1 | SAP B1 → AMS |
| Stock availability | SAP B1 | Query/read |
| Goods issue/return maintenance | SAP B1 | AMS → SAP B1 |
| Purchase request untuk part/jasa | SAP B1 | AMS → SAP B1 |
| A/P Invoice vendor | SAP B1 | SAP B1 → AMS reference |
| Request, schedule, checklist, failure | AMS | Internal |
| Work order dan maintenance history | AMS | Internal |

Posting inventory/financial tidak dilakukan dengan menulis langsung ke database SAP B1. Gunakan Service Layer, DI API, B1iF, atau integration middleware yang disetujui.

## 35.20 KPI maintenance

KPI minimum:

```text
Request backlog
Overdue request
Open work order
Schedule compliance
Preventive maintenance compliance
SLA response compliance
SLA resolution compliance
Mean Time to Respond (MTTRsp)
Mean Time to Repair (MTTR)
Mean Time Between Failures (MTBF)
Repeat failure rate
Planned vs unplanned maintenance ratio
Asset downtime
Maintenance cost per asset
Maintenance cost vs replacement value
Part consumption
First-time fix rate
Vendor SLA performance
Checklist finding closure rate
```

Rumus dasar:

```text
MTTR = total repair duration / number of completed repairs
MTBF = total operating time / number of failures
Schedule compliance = completed on schedule / scheduled work orders × 100%
First-time fix rate = resolved without repeat/follow-up / resolved work orders × 100%
```

Definisi jam operasi dan failure harus disepakati agar KPI tidak menyesatkan.

## 35.21 Tahapan implementasi maintenance

### Tahap M1 — Corrective maintenance

- priority;
- request dan triage;
- laporan gangguan/failure;
- work order;
- team dan assignment karyawan;
- jadwal manual/request-based;
- event/history;
- attachment dan notification.

### Tahap M2 — Preventive maintenance

- maintenance plan;
- calendar/meter trigger;
- scheduler idempotent;
- checklist template dan execution;
- finding dan request turunan;
- next-due calculation.

### Tahap M3 — Contract dan part

- contract/warranty coverage validation;
- SLA snapshot dan escalation;
- vendor personnel;
- spare part requirement/usage;
- integrasi SAP B1 goods issue, return, dan purchase request;
- cost tracking.

### Tahap M4 — Reliability dan optimization

- root cause analysis;
- MTBF/MTTR;
- downtime dan production loss;
- predictive/condition-based trigger;
- vendor scorecard;
- replacement recommendation berbasis cost, failure, dan lifecycle.

## 35.22 Definition of Done domain maintenance

Domain maintenance siap dikembangkan ketika:

- state machine request, schedule, work order, finding, dan failure disepakati;
- priority matrix dan SLA mapping disetujui;
- sumber master employee, vendor, item, dan warehouse ditetapkan;
- aturan cakupan contract/warranty dapat diuji;
- checklist versioning dan aturan temuan kritis ditetapkan;
- proses issue/return part ke SAP B1 diputuskan;
- perhitungan downtime, MTTR, dan MTBF memiliki definisi bisnis;
- transaction boundary dan idempotency scheduler diuji;
- role dan separation of duties disetujui;
- sample scenario mencakup request manual, urgent breakdown, preventive schedule, vendor contract, finding checklist, dan part replacement;
- histori aset dapat ditelusuri dari request sampai close dan transaksi SAP B1 terkait.

---

# 36. Physical Asset Tracking: RFID, QR Code, Location, dan Movement

## 36.1 Tujuan dan batas domain

Domain ini memastikan aplikasi dapat:

- mengidentifikasi aset menggunakan QR Code, barcode, RFID HF/NFC, atau RFID UHF;
- memverifikasi keberadaan aset di lokasi yang seharusnya;
- merekam scan individual maupun stock opname massal;
- mendeteksi aset berada di lokasi berbeda dari lokasi tercatat;
- mengelola perpindahan sementara dan permanen;
- meminta approval, konfirmasi pengiriman, dan konfirmasi penerimaan;
- memperbarui lokasi serta custodian hanya setelah transaksi yang sah;
- menghasilkan laporan movement, overdue return, unverified, missing, dan location discrepancy;
- mengaitkan aset kepada karyawan sebagai penanggung jawab atau pengguna.

QR/RFID adalah **media identifikasi**, bukan sumber kebenaran lokasi. Lokasi resmi tetap berasal dari transfer yang selesai atau hasil rekonsiliasi stock opname yang telah disetujui.

## 36.2 Model identitas/tag aset

Satu aset dapat memiliki beberapa tag sepanjang lifecycle karena tag dapat rusak, hilang, diganti, atau teknologinya berubah.

```text
asset_tags
----------
id UUID PK
asset_id UUID FK
tag_type VARCHAR(20)
tag_uid VARCHAR(255)
printed_value VARCHAR(255) NULL
epc_code VARCHAR(255) NULL
status VARCHAR(20)
issued_at TIMESTAMPTZ
activated_at TIMESTAMPTZ NULL
deactivated_at TIMESTAMPTZ NULL
replaced_tag_id UUID FK NULL
issued_by UUID
notes TEXT NULL
```

Nilai `tag_type`:

```text
QR_CODE
BARCODE
RFID_HF
RFID_UHF
NFC
```

Nilai `status`:

```text
ISSUED
ACTIVE
DAMAGED
LOST
REPLACED
DEACTIVATED
```

Constraint:

```sql
UNIQUE (tag_type, tag_uid);
CHECK (deactivated_at IS NULL OR deactivated_at >= issued_at);
```

Gunakan partial unique index agar satu aset hanya memiliki satu tag aktif untuk satu tipe:

```sql
CREATE UNIQUE INDEX uq_asset_active_tag_type
ON asset_tags (asset_id, tag_type)
WHERE status = 'ACTIVE';
```

`assets.qr_code`, `assets.barcode`, dan `assets.tag_number` dapat dipertahankan sementara untuk kompatibilitas/import, tetapi sumber utama tag operasional adalah `asset_tags`.

Payload QR publik tidak boleh memuat harga, nama karyawan, serial number sensitif, atau kredensial. Gunakan opaque identifier atau signed token yang dipetakan oleh API.

## 36.3 Perangkat pembaca dan titik scan

```text
tracking_devices
----------------
id UUID PK
device_code VARCHAR(50) UNIQUE
device_name VARCHAR(150)
device_type VARCHAR(30)
serial_number VARCHAR(150) NULL
location_id UUID FK NULL
is_fixed_reader BOOLEAN
reader_direction VARCHAR(20) NULL
last_seen_at TIMESTAMPTZ NULL
status VARCHAR(20)
api_credential_reference VARCHAR(255) NULL
```

Contoh `device_type`:

```text
MOBILE_CAMERA
HANDHELD_RFID
FIXED_RFID_GATE
NFC_PHONE
DESKTOP_SCANNER
```

Fixed RFID reader wajib melekat pada `location_id`. Mobile scanner dapat memperoleh lokasi dari lokasi yang dipilih operator dan, bila tersedia, GPS perangkat.

## 36.4 Event scan yang immutable

Setiap pembacaan disimpan sebagai event mentah dan tidak diubah setelah tercatat.

```text
asset_scan_events
-----------------
id UUID PK
event_uid UUID UNIQUE
asset_id UUID FK NULL
asset_tag_id UUID FK NULL
raw_tag_uid VARCHAR(255)
scan_type VARCHAR(30)
scan_source VARCHAR(30)
device_id UUID FK NULL
scanned_location_id UUID FK NULL
latitude NUMERIC(10,7) NULL
longitude NUMERIC(10,7) NULL
gps_accuracy_meters NUMERIC(10,2) NULL
scanned_at TIMESTAMPTZ
received_at TIMESTAMPTZ
scanned_by UUID NULL
transfer_id UUID FK NULL
stocktake_session_id UUID FK NULL
match_status VARCHAR(30)
processing_status VARCHAR(20)
metadata JSONB NULL
```

Nilai `scan_type`:

```text
VERIFY
DISPATCH
RECEIVE
CHECK_IN
CHECK_OUT
STOCKTAKE
RFID_GATE_ENTRY
RFID_GATE_EXIT
MAINTENANCE_IN
MAINTENANCE_OUT
```

Nilai `match_status`:

```text
MATCHED
UNKNOWN_TAG
EXPECTED_LOCATION
UNEXPECTED_LOCATION
DUPLICATE
UNAUTHORIZED_MOVEMENT
```

`event_uid` menjadi idempotency key untuk menghadapi perangkat offline, retry, dan event RFID berulang. Event RFID duplikat dalam jendela waktu singkat boleh ditandai `DUPLICATE`, tetapi tidak dihapus.

## 36.5 Verifikasi lokasi dan keberadaan

```text
asset_verifications
-------------------
id UUID PK
asset_id UUID FK
scan_event_id UUID FK
expected_location_id UUID FK NULL
observed_location_id UUID FK NULL
verification_result VARCHAR(30)
verified_at TIMESTAMPTZ
verified_by UUID NULL
expected_custodian_id UUID FK NULL
observed_custodian_id UUID FK NULL
resolution_status VARCHAR(20)
resolved_by UUID NULL
resolved_at TIMESTAMPTZ NULL
resolution_action VARCHAR(30) NULL
notes TEXT NULL
```

Hasil verifikasi:

```text
PRESENT_MATCH
PRESENT_WRONG_LOCATION
PRESENT_WRONG_CUSTODIAN
TAG_NOT_REGISTERED
ASSET_NOT_EXPECTED
NOT_FOUND
```

Jika scan menunjukkan lokasi berbeda, sistem **tidak langsung** mengubah `assets.current_location_id`. Sistem membuat discrepancy yang harus:

1. dikaitkan ke transfer yang masih berjalan;
2. dikoreksi sebagai kesalahan scan;
3. dibuatkan transfer retroaktif dengan approval; atau
4. dieskalasi sebagai unauthorized movement/lost asset.

## 36.6 Stock opname berbasis QR/RFID

```text
asset_stocktake_sessions
------------------------
id UUID PK
session_number VARCHAR(50) UNIQUE
location_id UUID FK
scope_type VARCHAR(20)
status VARCHAR(20)
planned_start_at TIMESTAMPTZ
planned_end_at TIMESTAMPTZ NULL
started_at TIMESTAMPTZ NULL
completed_at TIMESTAMPTZ NULL
created_by UUID
approved_by UUID NULL
approved_at TIMESTAMPTZ NULL
notes TEXT NULL

asset_stocktake_expected_items
------------------------------
id UUID PK
stocktake_session_id UUID FK
asset_id UUID FK
expected_location_id UUID FK
expected_custodian_id UUID FK NULL
snapshot_status VARCHAR(30)

asset_stocktake_results
-----------------------
id UUID PK
stocktake_session_id UUID FK
asset_id UUID FK NULL
scan_event_id UUID FK NULL
result_type VARCHAR(30)
observed_location_id UUID FK NULL
observed_at TIMESTAMPTZ NULL
resolution_status VARCHAR(20)
resolution_reference_type VARCHAR(30) NULL
resolution_reference_id UUID NULL
notes TEXT NULL
```

`result_type`:

```text
FOUND
MISSING
UNEXPECTED
WRONG_LOCATION
DUPLICATE_TAG
UNKNOWN_TAG
```

Expected item harus di-snapshot saat sesi dimulai agar laporan tidak berubah ketika master aset berubah di tengah stock opname.

## 36.7 Workflow perpindahan aset

`asset_transfers.transfer_type`:

```text
PERMANENT_RELOCATION
TEMPORARY_LOAN
MAINTENANCE_DELIVERY
RETURN_FROM_MAINTENANCE
EMPLOYEE_HANDOVER
INTER_BRANCH
INTER_COMPANY
```

State machine:

```text
DRAFT
→ SUBMITTED
→ APPROVED
→ DISPATCHED
→ IN_TRANSIT
→ RECEIVED
→ COMPLETED
```

Jalur pengecualian:

```text
SUBMITTED → REJECTED
APPROVED  → CANCELLED
DISPATCHED/IN_TRANSIT → DISPUTED
```

Aturan permanen:

- `is_permanent = TRUE`;
- wajib ada approval sesuai matriks kewenangan;
- penerima wajib memindai QR/RFID dan mengonfirmasi kondisi;
- `current_location_id` dan custodian baru berubah saat item `RECEIVED/COMPLETED`;
- histori lokasi/assignment lama ditutup dan histori baru dibuat dalam satu transaksi;
- jika antar-company, integrasi/rekonsiliasi SAP B1 diproses sesuai kebijakan finansial.

Aturan sementara:

- `is_permanent = FALSE`;
- `expected_return_at` wajib;
- lokasi aktual dapat berubah, tetapi home/base location tetap dapat disimpan terpisah;
- sistem membuat reminder overdue;
- pengembalian memerlukan scan `CHECK_IN` atau transfer balik.

## 36.8 Konfirmasi transfer dan serah terima

```text
asset_transfer_confirmations
----------------------------
id UUID PK
asset_transfer_id UUID FK
asset_transfer_item_id UUID FK NULL
confirmation_type VARCHAR(30)
confirmed_by UUID
confirmed_at TIMESTAMPTZ
scan_event_id UUID FK NULL
condition_status VARCHAR(30) NULL
latitude NUMERIC(10,7) NULL
longitude NUMERIC(10,7) NULL
notes TEXT NULL
```

`confirmation_type`:

```text
APPROVAL
DISPATCH_HANDOVER
RECEIPT_ACCEPTANCE
PERMANENT_MOVE_CONFIRMATION
RETURN_ACCEPTANCE
DISCREPANCY_ACKNOWLEDGEMENT
```

Untuk aset kritis, sistem dapat mensyaratkan dual control: pengirim dan penerima tidak boleh orang yang sama.

## 36.9 Assignment kepada karyawan

Desain sudah mendukung aset melekat kepada karyawan melalui `asset_assignments`.

Peran dibedakan sebagai berikut:

| Assignment type | Makna |
|---|---|
| `PRIMARY_CUSTODIAN` | Penanggung jawab administratif atas keberadaan dan kondisi aset |
| `USER` | Karyawan yang memakai aset sehari-hari |
| `TECHNICAL_PIC` | Penanggung jawab teknis/pemeliharaan |
| `DEPARTMENT_CONTROL` | Aset dikuasai unit, bukan satu karyawan |
| `TEMPORARY_BORROWER` | Pemakai sementara dengan tanggal kembali |

Satu karyawan dapat memegang banyak aset. Satu aset dapat memiliki beberapa assignment berbeda pada saat yang sama, tetapi hanya satu `PRIMARY_CUSTODIAN` aktif.

Serah terima kepada karyawan:

1. requester membuat transfer/assignment;
2. approver menyetujui bila diperlukan;
3. aset dipindai saat diserahkan;
4. penerima mengonfirmasi penerimaan dan kondisi;
5. assignment lama ditutup;
6. assignment baru menjadi `ACTIVE`;
7. dokumen serah terima dan audit event disimpan.

Berakhirnya hubungan kerja atau mutasi karyawan harus memicu daftar aset aktif yang wajib dikembalikan/dialihkan sebelum clearance selesai.

## 36.10 Movement alert dan exception

```text
asset_tracking_alerts
---------------------
id UUID PK
asset_id UUID FK NULL
scan_event_id UUID FK NULL
alert_type VARCHAR(30)
severity VARCHAR(20)
detected_at TIMESTAMPTZ
status VARCHAR(20)
assigned_to UUID NULL
acknowledged_at TIMESTAMPTZ NULL
resolved_at TIMESTAMPTZ NULL
resolution_code VARCHAR(30) NULL
notes TEXT NULL
```

Contoh `alert_type`:

```text
UNAUTHORIZED_MOVEMENT
WRONG_LOCATION
UNKNOWN_TAG
TAG_DUPLICATION
ASSET_NOT_FOUND
OVERDUE_RETURN
RFID_GATE_WITHOUT_TRANSFER
UNVERIFIED_TOO_LONG
```

Fixed RFID gate hanya memunculkan indikasi pergerakan. Sistem mencocokkannya dengan transfer aktif, maintenance work order, atau izin keluar. Tanpa referensi yang sah, event membentuk alert dan tidak otomatis dianggap perpindahan permanen.

## 36.11 Transaction boundary perpindahan permanen

Completion transfer harus atomic:

1. lock `asset_transfers`, item, dan row `assets`;
2. validasi approval, dispatch scan, receipt scan, penerima, dan kondisi;
3. pastikan aset masih berada di lokasi asal yang diharapkan;
4. tutup `asset_location_histories` aktif;
5. insert histori lokasi tujuan;
6. tutup assignment custodian lama bila berubah;
7. buat/aktifkan assignment custodian baru;
8. update cache `assets.current_location_id` dan `current_primary_custodian_id`;
9. update `last_verified_at` dan `last_verified_location_id`;
10. buat status history, notification, integration outbox bila perlu, dan audit log;
11. commit.

Optimistic locking menggunakan `assets.version_no`; operasi bersamaan mengembalikan `409 CONFLICT`.

## 36.12 API FastAPI awal

```text
POST   /api/v1/asset-tags
POST   /api/v1/asset-tags/{tag_id}/replace
POST   /api/v1/tracking/scan-events
POST   /api/v1/tracking/scan-events/batch
GET    /api/v1/assets/{asset_id}/tracking
GET    /api/v1/assets/{asset_id}/movement-history

POST   /api/v1/asset-transfers
POST   /api/v1/asset-transfers/{id}/submit
POST   /api/v1/asset-transfers/{id}/approve
POST   /api/v1/asset-transfers/{id}/dispatch
POST   /api/v1/asset-transfers/{id}/receive
POST   /api/v1/asset-transfers/{id}/confirm-permanent
POST   /api/v1/asset-transfers/{id}/complete
POST   /api/v1/asset-transfers/{id}/return

POST   /api/v1/stocktakes
POST   /api/v1/stocktakes/{id}/start
POST   /api/v1/stocktakes/{id}/scan
POST   /api/v1/stocktakes/{id}/complete
POST   /api/v1/stocktakes/{id}/approve

GET    /api/v1/reports/asset-movements
GET    /api/v1/reports/location-discrepancies
GET    /api/v1/reports/missing-assets
GET    /api/v1/reports/overdue-returns
GET    /api/v1/reports/custodian-assets
GET    /api/v1/reports/unverified-assets
```

Scan batch wajib mendukung offline synchronization dengan:

- client-generated `event_uid`;
- timestamp perangkat dan timestamp server;
- idempotent upsert;
- batas toleransi clock drift;
- autentikasi perangkat/operator;
- respons per item untuk accepted, duplicate, rejected, dan unknown tag.

## 36.13 Struktur modul FastAPI

```text
app/modules/asset_tracking/
├── models/
│   ├── asset_tag.py
│   ├── tracking_device.py
│   ├── scan_event.py
│   ├── verification.py
│   ├── stocktake.py
│   └── tracking_alert.py
├── schemas/
│   ├── tag.py
│   ├── scan.py
│   ├── verification.py
│   ├── stocktake.py
│   └── report.py
├── routes/
│   ├── tags.py
│   ├── scans.py
│   ├── stocktakes.py
│   └── reports.py
├── services/
│   ├── tag_service.py
│   ├── scan_ingestion_service.py
│   ├── verification_service.py
│   ├── movement_matching_service.py
│   ├── stocktake_service.py
│   └── tracking_alert_service.py
├── repositories/
├── enums/
└── tests/
```

Workflow transfer tetap berada pada modul `asset_transfer`, sedangkan `asset_tracking` menyediakan bukti scan dan deteksi exception. Hindari mencampur ingest event RFID berfrekuensi tinggi dengan transaksi approval.

## 36.14 Laporan pergerakan aset

Laporan movement minimal memuat:

| Kolom | Sumber |
|---|---|
| Asset code/name/tag | `assets`, `asset_tags` |
| Tanggal dan waktu | `asset_transfers`, `asset_scan_events` |
| Lokasi asal/tujuan | `asset_locations` |
| Jenis perpindahan | `asset_transfers.transfer_type` |
| Sementara/permanen | `asset_transfers.is_permanent` |
| Custodian lama/baru | `asset_transfer_items`, `asset_assignments` |
| Requester/approver/pengirim/penerima | transfer dan confirmations |
| Kondisi serah/terima | transfer item dan confirmations |
| Status movement | `asset_transfers.status` |
| Bukti scan | `asset_scan_events` |
| Keterlambatan kembali | `expected_return_at` dibanding waktu aktual |

Filter minimal: periode, company, branch, department, location, asset category, employee, transfer type, permanen/sementara, dan status.

## 36.15 Integrasi SAP Business One

System of Record:

| Data | System of Record |
|---|---|
| Lokasi fisik detail, scan, custodian, movement operasional | Asset Management |
| Warehouse/bin yang berdampak persediaan | SAP B1, direkonsiliasi dari transfer sah |
| Nilai aset, depresiasi, kapitalisasi | SAP B1 |
| Employee reference | Sumber HR/SAP B1 sesuai keputusan integrasi |

Tidak semua perpindahan ruangan perlu dikirim ke SAP B1. Sinkronisasi dilakukan bila movement mengubah dimensi yang relevan bagi SAP, misalnya company, branch, warehouse, bin, cost center, atau penanggung jawab yang memang dipetakan.

## 36.16 Security dan privacy

- scan memerlukan autentikasi operator atau device credential;
- device credential disimpan sebagai secret reference, bukan plaintext;
- akses lokasi GPS dibatasi dan memiliki retention policy;
- laporan custodian tunduk pada role/organizational scope;
- tag replacement, transfer approval, discrepancy override, dan stocktake approval diaudit;
- pengguna tidak boleh mengonfirmasi approval atas request sendiri bila separation of duties diterapkan;
- endpoint ingest diberi rate limit dan replay protection.

## 36.17 Index dan partitioning

```sql
CREATE INDEX ix_scan_asset_time
ON asset_scan_events (asset_id, scanned_at DESC);

CREATE INDEX ix_scan_tag_time
ON asset_scan_events (asset_tag_id, scanned_at DESC);

CREATE INDEX ix_scan_location_time
ON asset_scan_events (scanned_location_id, scanned_at DESC);

CREATE INDEX ix_transfer_status_date
ON asset_transfers (status, transfer_date DESC);

CREATE INDEX ix_assignment_employee_active
ON asset_assignments (employee_id, assignment_type)
WHERE returned_at IS NULL;
```

`asset_scan_events` berpotensi sangat besar, terutama untuk RFID fixed reader. Pertimbangkan monthly range partitioning, retention raw event, dan summary table tanpa menghapus jejak audit yang diwajibkan.

## 36.18 Tahapan implementasi tracking

### T1 — QR dan assignment

- tag registry dan QR generation;
- mobile/web scan;
- custodian/user assignment;
- transfer permanen dan sementara;
- approval, dispatch, receipt, dan serah terima;
- movement history dan custodian report.

### T2 — Stock opname

- session dan expected snapshot;
- batch/offline scan;
- found/missing/unexpected/wrong location;
- discrepancy resolution dan approval;
- reminder unverified/overdue.

### T3 — RFID

- handheld RFID;
- device registry;
- fixed gate event ingestion;
- duplicate suppression;
- movement matching dan alert.

### T4 — Optimization

- dashboard movement;
- heatmap aset per lokasi;
- anomaly detection;
- verification frequency berbasis criticality;
- integrasi warehouse/bin/cost center SAP B1.

## 36.19 Definition of Done domain tracking

Domain tracking siap dikembangkan ketika:

- format QR/tag UID dan kebijakan replacement disepakati;
- tipe reader dan pola konektivitas perangkat ditentukan;
- location hierarchy dan GPS policy disetujui;
- state machine transfer serta matriks approval disepakati;
- perbedaan transfer permanen, pinjam sementara, maintenance delivery, dan return jelas;
- aturan custodian versus user disetujui;
- konfirmasi pengirim/penerima dan condition handover dapat diuji;
- offline scan idempotency dan duplicate RFID handling diuji;
- stocktake snapshot serta resolution discrepancy disepakati;
- current location hanya berubah melalui transaction boundary yang sah;
- laporan movement, custodian, missing, wrong location, overdue, dan unverified lulus acceptance test;
- perubahan yang relevan ke SAP B1 menggunakan outbox, idempotency, retry, dan rekonsiliasi.

---

# 37. Standar Arsitektur Backend FastAPI

## 37.1 Keputusan teknologi

Backend dikembangkan sebagai **modular monolith**. Setiap domain memiliki folder,
model, schema, repository, service, route, policy, dan test sendiri. Pendekatan
ini memberi batas domain yang tegas tanpa menambah kompleksitas distributed
transaction seperti pada microservices.

| Komponen | Standar |
|---|---|
| Runtime | Python 3.12 atau versi yang tervalidasi oleh tim |
| Web framework | FastAPI |
| Database | PostgreSQL 18 |
| ORM | SQLAlchemy 2.x async |
| Driver aplikasi | `asyncpg` |
| Driver migration/admin | `psycopg` |
| Migration | Alembic |
| Validasi | Pydantic 2 + pydantic-settings |
| Primary key | UUID native PostgreSQL |
| Authentication | JWT access token dan refresh token |
| API prefix | `/api/v1` |
| API documentation | OpenAPI/Swagger dari FastAPI |

UUID dibuat oleh aplikasi menggunakan `uuid.uuid4()` atau UUIDv7 bila
standardisasi library UUIDv7 telah disepakati. Kolom database tetap menggunakan
tipe native PostgreSQL `UUID`, bukan `VARCHAR(36)`.

```python
from uuid import UUID, uuid4
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

id: Mapped[UUID] = mapped_column(
    Uuid(as_uuid=True),
    primary_key=True,
    default=uuid4,
)
```

UUID mempermudah import, sinkronisasi, dan penggabungan data lintas instalasi,
tetapi **bukan** pengganti business identifier. Asset tetap memiliki
`asset_code`, request memiliki `request_number`, dan work order memiliki
`work_order_number`.

## 37.2 Struktur direktori aplikasi

```text
asset-management-api/
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── .env.example
├── README.md
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── middleware/
│   │   ├── cors.py
│   │   ├── request_context.py
│   │   ├── exception_handler.py
│   │   └── security_headers.py
│   ├── shared/
│   │   ├── enums.py
│   │   ├── schemas.py
│   │   ├── responses.py
│   │   ├── pagination.py
│   │   ├── filters.py
│   │   ├── types.py
│   │   └── utils.py
│   ├── modules/
│   │   ├── identity/
│   │   ├── organizations/
│   │   ├── employees/
│   │   ├── partners/
│   │   ├── assets/
│   │   ├── locations/
│   │   ├── assignments/
│   │   ├── acquisitions/
│   │   ├── depreciation/
│   │   ├── warranties/
│   │   ├── leases/
│   │   ├── software_licenses/
│   │   ├── maintenance_contracts/
│   │   ├── maintenance/
│   │   ├── tracking/
│   │   ├── lifecycle/
│   │   ├── meters/
│   │   ├── documents/
│   │   ├── notifications/
│   │   ├── sap_integration/
│   │   └── audit/
│   └── workers/
│       ├── scheduler.py
│       ├── sap_sync.py
│       └── notifications.py
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── e2e/
```

Setiap modul menggunakan struktur baku:

```text
app/modules/assets/
├── __init__.py
├── constants.py
├── dependencies.py
├── exceptions.py
├── models.py
├── policies.py
├── repository.py
├── routes.py
├── schemas.py
├── service.py
└── events.py
```

Jika modul menjadi besar, file boleh dipecah menjadi package tanpa mengubah
tanggung jawab lapisan:

```text
maintenance/
├── models/
├── schemas/
├── repositories/
├── services/
├── routes/
└── policies/
```

## 37.3 Tanggung jawab setiap lapisan

| Lapisan | Boleh melakukan | Tidak boleh melakukan |
|---|---|---|
| Routes | Parse request, dependency injection, HTTP status, response envelope | Query langsung, commit, business rule kompleks |
| Schemas | Validasi request/response, serialisasi, kontrak API | Query database atau side effect |
| Service | Use case, workflow, transaction boundary, rule lintas repository | Bergantung pada object HTTP |
| Repository | Query, persistence, eager loading, lock | Menentukan workflow bisnis |
| Models | Mapping tabel, FK, relationship, constraint | Menjadi schema API |
| Policies | Pemeriksaan permission dan scope data | Mengubah data |
| Events | Kontrak domain/outbox event | Menjalankan integrasi eksternal langsung |

Alur dependency harus searah:

```text
routes → service → repository → SQLAlchemy model → PostgreSQL
```

Modul tidak boleh mengakses repository privat modul lain secara langsung.
Gunakan public service modul tujuan atau domain event. Pengecualian hanya untuk
read model/reporting yang didokumentasikan secara eksplisit.

## 37.4 Database dan SQLAlchemy

`app/core/database.py` menyediakan:

- async engine;
- `async_sessionmaker`;
- satu `AsyncSession` per request;
- health check database;
- konfigurasi pool dari environment;
- rollback otomatis bila exception;
- unit-of-work untuk service dan worker.

```python
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

Service menentukan batas transaksi:

```python
async with session.begin():
    asset = await asset_repository.get_for_update(asset_id)
    transfer = await transfer_repository.create(command)
    await asset_repository.apply_confirmed_transfer(asset, transfer)
    await outbox_repository.add(transfer.to_event())
```

Aturan:

- `commit()` tidak dilakukan di route atau repository;
- eager/lazy loading ditentukan repository secara eksplisit;
- query list selalu mendukung pagination dan batas maksimum;
- `SELECT ... FOR UPDATE` digunakan untuk workflow yang rawan race condition;
- optimistic locking digunakan pada aggregate penting;
- timestamp disimpan sebagai `TIMESTAMPTZ` dalam UTC;
- nominal menggunakan `NUMERIC`, bukan `FLOAT`;
- enum kritis menggunakan `VARCHAR` + check constraint atau PostgreSQL enum
  berdasarkan strategi migration yang disepakati;
- soft delete hanya digunakan bila kebutuhan audit mengharuskannya;
- audit log dan event scan tidak boleh diubah setelah dibuat.

## 37.5 Alembic dan migrasi

Alembic adalah satu-satunya mekanisme perubahan schema. Aplikasi tidak boleh
menjalankan `Base.metadata.create_all()` pada production.

Konvensi migration:

```text
YYYYMMDD_HHMM_<domain>_<description>.py
```

Contoh:

```text
20260727_1910_assets_add_asset_registry.py
20260727_1930_maintenance_add_work_orders.py
```

Workflow:

```bash
alembic revision --autogenerate -m "assets add asset registry"
alembic upgrade head
alembic downgrade -1
alembic current
alembic heads
```

Setiap migration wajib:

- direview agar tidak ada drop/rename tidak disengaja;
- memiliki `upgrade()` dan `downgrade()` yang realistis;
- menggunakan migration terpisah untuk backfill data besar;
- menjaga data lama ketika menambah kolom wajib: nullable → backfill → not null;
- menguji upgrade dari schema production terakhir;
- menguji bahwa hanya ada satu Alembic head sebelum release;
- tidak mengubah migration yang sudah pernah dipakai di environment bersama.

`alembic/env.py` harus mengimpor seluruh metadata model melalui satu registry
agar `--autogenerate` dapat mendeteksi semua tabel modul.

## 37.6 Konfigurasi environment

Seluruh konfigurasi berada di environment dan dibaca dengan
`pydantic-settings`. Secret tidak disimpan di source code.

```dotenv
APP_NAME=Asset Management API
APP_ENV=development
APP_DEBUG=false
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/asset_management
DATABASE_MIGRATION_URL=postgresql+psycopg://user:password@localhost:5432/asset_management
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE_SECONDS=1800

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=15
JWT_REFRESH_TOKEN_DAYS=7
JWT_ISSUER=asset-management-api
JWT_AUDIENCE=asset-management-client

CORS_ALLOWED_ORIGINS=["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true
TRUSTED_HOSTS=["localhost"]

SAP_BASE_URL=
SAP_COMPANY_DB=
SAP_USERNAME=
SAP_PASSWORD=
SAP_VERIFY_SSL=true
```

Untuk production, bila tersedia, gunakan asymmetric JWT (`RS256`/`ES256`) dan
secret manager. `.env` hanya untuk local development dan harus masuk
`.gitignore`; repository hanya menyimpan `.env.example`.

## 37.7 Middleware

Urutan konseptual middleware:

```text
Trusted host/security headers
→ CORS
→ request ID/context
→ access log/timing
→ authentication dependency
→ route
→ exception normalization
→ JSON response baku
```

### CORS

- origin diambil dari konfigurasi, bukan `*` pada production;
- bila credentials aktif, wildcard origin tidak diperbolehkan;
- method dan header yang diperbolehkan ditetapkan eksplisit;
- konfigurasi CORS hanya di satu lapisan untuk menghindari header ganda antara
  FastAPI dan Nginx;
- preflight `OPTIONS` harus dapat selesai tanpa JWT.

### Request context

Setiap request memiliki `request_id` UUID. Nilai dari `X-Request-ID` boleh
dipakai hanya setelah divalidasi; jika tidak tersedia, server membuat ID baru.
ID dikembalikan pada header dan `meta.request_id`, serta dicatat di log, audit,
outbox, dan error.

### Exception normalization

Register handler global untuk:

- `RequestValidationError`;
- `HTTPException`;
- authentication/authorization error;
- domain/business exception;
- SQLAlchemy integrity error yang telah dipetakan;
- exception tak terduga.

Stack trace tidak boleh dikirim ke client pada production.

## 37.8 JWT authentication dan authorization

JWT bukan middleware untuk business authorization. JWT memverifikasi identitas;
route dependency dan policy memeriksa hak akses serta data scope.

Access token minimal memuat:

```json
{
  "sub": "user-uuid",
  "jti": "token-uuid",
  "type": "access",
  "iss": "asset-management-api",
  "aud": "asset-management-client",
  "iat": 1785150000,
  "nbf": 1785150000,
  "exp": 1785150900
}
```

Role/permission boleh dimuat sebagai claim ringkas, tetapi authorization kritis
tetap divalidasi terhadap database agar perubahan hak tidak menunggu token
kedaluwarsa.

Endpoint awal:

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Aturan keamanan:

- password di-hash menggunakan Argon2;
- refresh token disimpan dalam bentuk hash dan dapat dicabut;
- token dibedakan dengan claim `type`;
- validasi signature, `exp`, `nbf`, `iss`, `aud`, dan `jti`;
- rotasi refresh token pada setiap refresh;
- reuse refresh token yang sudah dipakai mencabut token family;
- rate limit diterapkan pada login dan refresh;
- semua authentication event masuk audit log;
- token dan password tidak pernah dicatat di log;
- `401` untuk identitas/token tidak valid, `403` untuk permission tidak cukup.

## 37.9 JSON response baku

Semua endpoint, termasuk health check dan error, memakai envelope yang sama.

### Sukses tunggal

```json
{
  "success": true,
  "message": "Asset berhasil dibuat.",
  "data": {
    "id": "f5e1da0e-b5cf-4c48-91e1-e7efc1b266fe"
  },
  "error": null,
  "meta": {
    "request_id": "702a2b31-7752-4186-b5b1-775a848857ac",
    "timestamp": "2026-07-27T12:30:00Z",
    "api_version": "v1"
  }
}
```

### Sukses list

```json
{
  "success": true,
  "message": "Daftar asset berhasil diambil.",
  "data": [],
  "error": null,
  "meta": {
    "request_id": "702a2b31-7752-4186-b5b1-775a848857ac",
    "timestamp": "2026-07-27T12:30:00Z",
    "api_version": "v1",
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 0,
      "total_pages": 0,
      "has_next": false,
      "has_previous": false
    }
  }
}
```

### Error

```json
{
  "success": false,
  "message": "Permintaan tidak dapat diproses.",
  "data": null,
  "error": {
    "code": "ASSET_PRIMARY_CUSTODIAN_EXISTS",
    "message": "Asset telah memiliki penanggung jawab aktif.",
    "details": [
      {
        "field": "employee_id",
        "reason": "active_assignment_conflict"
      }
    ]
  },
  "meta": {
    "request_id": "702a2b31-7752-4186-b5b1-775a848857ac",
    "timestamp": "2026-07-27T12:30:00Z",
    "api_version": "v1"
  }
}
```

Schema generik:

```python
T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | dict[str, Any] | None = None

class ResponseMeta(BaseModel):
    request_id: UUID
    timestamp: datetime
    api_version: str
    pagination: PaginationMeta | None = None

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta
```

Invariant:

- jika `success=true`, `error` harus `null`;
- jika `success=false`, `data` harus `null`;
- error `code` bersifat stabil dan dapat dipakai frontend;
- `message` boleh diterjemahkan, tetapi `code` tidak berubah;
- response `204 No Content` dilarang bila envelope diwajibkan; operasi delete
  menggunakan `200` dengan response baku;
- file download dan streaming boleh menjadi pengecualian yang terdokumentasi;
- OpenAPI setiap route harus mendeklarasikan schema sukses dan error.

## 37.10 Pagination, filter, dan sorting

Kontrak list:

```text
page=1
page_size=20
sort=asset_code
order=asc
search=laptop
```

Aturan:

- `page_size` default 20, maksimum 100;
- kolom sort menggunakan allowlist;
- filter domain menggunakan parameter eksplisit;
- pencarian bebas tidak boleh membentuk SQL mentah;
- response list selalu mengandung `meta.pagination`;
- untuk event/scan berukuran sangat besar, cursor pagination lebih disarankan.

## 37.11 Startup dan router registration

`app/main.py` hanya melakukan composition:

```python
def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app

app = create_app()
```

`app/api/router.py` menggabungkan router modul. File ini tidak mengandung
business logic.

## 37.12 Dependency management

Daftar dependency baseline disediakan dalam file
`requirements_asset_management_fastapi.txt`. Version pin final harus dibuat
setelah compatibility test pada Python yang dipilih. Untuk production,
disarankan menghasilkan lock/hash melalui `pip-tools`:

```bash
pip-compile --generate-hashes requirements.in
pip-sync requirements.txt
```

Dependency yang tidak digunakan tidak boleh dipertahankan. Secara khusus:

- `aiosqlite` tidak dibutuhkan karena target database PostgreSQL;
- `psycopg2-binary` tidak perlu bila sudah menggunakan `psycopg` v3;
- gunakan satu library JWT, bukan beberapa implementasi sekaligus;
- `bcrypt` tidak diperlukan bila password hashing distandardisasi ke Argon2;
- worker queue seperti Celery/Redis baru diaktifkan bila deployment memang
  membutuhkan distributed background job.

## 37.13 Testing dan quality gate

Minimal pipeline:

```text
Ruff lint/format
→ mypy
→ unit tests
→ PostgreSQL integration tests
→ Alembic upgrade test
→ API contract tests
→ security/dependency scan
```

Test wajib mencakup:

- semua bentuk response sukses dan error;
- mapping validasi Pydantic menjadi envelope baku;
- login, refresh rotation, logout, expired/revoked token;
- role dan scope company/branch/department;
- rollback transaction ketika proses gagal;
- concurrency transfer, assignment, work order, dan RFID scan;
- migration database kosong dan upgrade dari versi sebelumnya;
- repository menggunakan PostgreSQL 18 pada integration test;
- endpoint tidak membocorkan stack trace atau secret.

## 37.14 Definition of Done arsitektur backend

- setiap domain berada dalam folder modul independen;
- routes, schemas, services, repositories, models, policies, dan exceptions
  terpisah;
- tidak ada query SQLAlchemy di route;
- tidak ada commit di route/repository;
- seluruh primary key menggunakan UUID native PostgreSQL;
- seluruh perubahan schema menggunakan Alembic;
- PostgreSQL 18 digunakan untuk integration test;
- CORS berasal dari allowlist environment dan tidak diduplikasi di Nginx;
- semua response JSON mengikuti satu envelope;
- seluruh exception global dinormalisasi;
- JWT memvalidasi issuer, audience, expiry, type, dan revocation;
- authorization memeriksa role, permission, dan data scope;
- secrets tidak berada di repository atau log;
- dependency production terkunci dan telah melewati vulnerability scan;
- OpenAPI, unit test, integration test, dan migration test lulus.

---

# 38. Foto, Dokumen, dan Attachment

## 38.1 Tujuan desain

Asset Management harus mendukung penyimpanan bukti visual dan dokumen pada
seluruh lifecycle aset, bukan hanya pada master `assets`. Cakupan minimum:

- foto profil dan kondisi awal aset;
- foto nameplate, serial number, QR Code, dan RFID tag;
- invoice, berita acara, sertifikat, garansi, dan dokumen pengadaan;
- manual book, installation manual, maintenance manual, dan user guide;
- foto sebelum, selama, dan sesudah pemeliharaan;
- laporan hasil pemeliharaan dan sertifikat kalibrasi;
- foto laporan kerusakan, gangguan, failure, dan temuan checklist;
- foto komponen atau spare part yang rusak dan diganti;
- bukti serah-terima, perpindahan, stock opname, dan disposal.

File tidak disimpan sebagai binary besar di tabel transaksi PostgreSQL. Database
hanya menyimpan metadata dan object key. Isi file ditempatkan pada object
storage privat yang kompatibel dengan S3, seperti MinIO, AWS S3, atau layanan
setara.

## 38.2 Prinsip model data

Gunakan tiga kelompok tabel:

```text
files
├── file_versions
└── attachments
    └── attachment_annotations
```

- `files` adalah identitas logis dan metadata keamanan sebuah file;
- `file_versions` menyimpan setiap versi fisik file;
- `attachments` menghubungkan file ke entity bisnis dan memberi konteks;
- `attachment_annotations` opsional untuk catatan atau penandaan pada foto.

Model ini menggantikan penggunaan langsung `documents`/`document_links` pada
desain awal. Bila tabel tersebut sudah dibuat, lakukan migrasi data ke
`files`/`attachments`, bukan menjalankan dua model dokumen secara paralel.

## 38.3 Tabel `files`

```sql
files
-----
id UUID PK
tenant_id UUID FK NOT NULL
original_filename VARCHAR(255) NOT NULL
display_name VARCHAR(255) NOT NULL
file_kind VARCHAR(20) NOT NULL
mime_type VARCHAR(150) NOT NULL
extension VARCHAR(20) NULL
size_bytes BIGINT NOT NULL
checksum_sha256 CHAR(64) NOT NULL
storage_provider VARCHAR(30) NOT NULL
storage_bucket VARCHAR(100) NOT NULL
storage_object_key VARCHAR(500) NOT NULL
current_version_no INTEGER NOT NULL DEFAULT 1
scan_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
scan_result TEXT NULL
is_encrypted BOOLEAN NOT NULL DEFAULT TRUE
is_active BOOLEAN NOT NULL DEFAULT TRUE
uploaded_by UUID FK NOT NULL
uploaded_at TIMESTAMPTZ NOT NULL
deleted_by UUID FK NULL
deleted_at TIMESTAMPTZ NULL
retention_until DATE NULL
metadata JSONB NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
version INTEGER NOT NULL DEFAULT 1
```

`file_kind`:

```text
IMAGE
DOCUMENT
VIDEO
AUDIO
OTHER
```

`scan_status`:

```text
PENDING
CLEAN
INFECTED
FAILED
QUARANTINED
```

Constraint dan index:

```sql
CHECK (size_bytes > 0);
CHECK (current_version_no > 0);
UNIQUE (storage_bucket, storage_object_key);

CREATE INDEX ix_files_tenant_checksum
ON files (tenant_id, checksum_sha256);
```

Checksum digunakan untuk pemeriksaan integritas dan peringatan duplikasi. File
yang checksum-nya sama tidak otomatis digabung karena kebijakan retention,
akses, dan konteks bisnisnya dapat berbeda.

## 38.4 Versioning dokumen

Manual book, user guide, SOP, drawing, dan dokumen teknis dapat berubah versi.
Gunakan:

```sql
file_versions
-------------
id UUID PK
file_id UUID FK NOT NULL
version_no INTEGER NOT NULL
storage_bucket VARCHAR(100) NOT NULL
storage_object_key VARCHAR(500) NOT NULL
mime_type VARCHAR(150) NOT NULL
size_bytes BIGINT NOT NULL
checksum_sha256 CHAR(64) NOT NULL
change_notes TEXT NULL
uploaded_by UUID FK NOT NULL
uploaded_at TIMESTAMPTZ NOT NULL
is_current BOOLEAN NOT NULL DEFAULT FALSE

UNIQUE (file_id, version_no)
```

Hanya satu versi aktif per file:

```sql
CREATE UNIQUE INDEX uq_file_versions_current
ON file_versions (file_id)
WHERE is_current = TRUE;
```

Versi lama tidak dihapus ketika versi baru diunggah. Untuk dokumen yang
memerlukan approval, dapat ditambahkan `approval_status`, `approved_by`, dan
`approved_at`.

## 38.5 Tabel `attachments`

```sql
attachments
-----------
id UUID PK
tenant_id UUID FK NOT NULL
file_id UUID FK NOT NULL
entity_type VARCHAR(50) NOT NULL
entity_id UUID NOT NULL
attachment_category VARCHAR(50) NOT NULL
title VARCHAR(255) NULL
description TEXT NULL
captured_at TIMESTAMPTZ NULL
captured_by UUID FK NULL
latitude NUMERIC(9,6) NULL
longitude NUMERIC(9,6) NULL
sequence_no INTEGER NOT NULL DEFAULT 1
is_primary BOOLEAN NOT NULL DEFAULT FALSE
visibility VARCHAR(20) NOT NULL DEFAULT 'INTERNAL'
source VARCHAR(20) NOT NULL DEFAULT 'UPLOAD'
created_by UUID FK NOT NULL
created_at TIMESTAMPTZ NOT NULL
deleted_by UUID FK NULL
deleted_at TIMESTAMPTZ NULL
```

`entity_type` yang diizinkan minimal:

```text
ASSET
ASSET_ACQUISITION
ASSET_WARRANTY
ASSET_TRANSFER
ASSET_STOCKTAKE
MAINTENANCE_CONTRACT
MAINTENANCE_REQUEST
MAINTENANCE_WORK_ORDER
MAINTENANCE_EXECUTION
MAINTENANCE_FINDING
ASSET_FAILURE
PART_REPLACEMENT
ASSET_RETIREMENT
```

`attachment_category`:

```text
ASSET_PROFILE_PHOTO
ASSET_CONDITION_PHOTO
NAMEPLATE_PHOTO
SERIAL_NUMBER_PHOTO
QR_RFID_TAG_PHOTO
MANUAL_BOOK
USER_GUIDE
INSTALLATION_GUIDE
MAINTENANCE_MANUAL
TECHNICAL_DRAWING
DATASHEET
WARRANTY_DOCUMENT
INVOICE
CERTIFICATE
BEFORE_MAINTENANCE_PHOTO
DURING_MAINTENANCE_PHOTO
AFTER_MAINTENANCE_PHOTO
MAINTENANCE_REPORT
FAILURE_PHOTO
DAMAGE_PHOTO
FINDING_PHOTO
ROOT_CAUSE_EVIDENCE
REPLACED_PART_PHOTO
HANDOVER_DOCUMENT
MOVEMENT_EVIDENCE
STOCKTAKE_EVIDENCE
DISPOSAL_EVIDENCE
OTHER
```

`source`:

```text
UPLOAD
CAMERA
MOBILE_SCAN
SAP_SYNC
SYSTEM_GENERATED
```

Polymorphic `entity_type` dan `entity_id` memudahkan satu mekanisme attachment
dipakai oleh semua domain. Karena PostgreSQL tidak dapat membuat foreign key
langsung dari pasangan polymorphic tersebut, service harus memakai registry
entity yang diizinkan dan memvalidasi keberadaan entity dalam transaksi yang
sama.

Alternatif dengan FK fisik terpisah dapat digunakan pada instalasi yang
memprioritaskan referential integrity penuh, tetapi akan menghasilkan banyak
tabel link. Baseline ini memilih attachment generik dengan validasi ketat di
service dan integration test.

## 38.6 Foto utama aset

Satu aset dapat memiliki banyak foto, tetapi maksimal satu foto utama aktif:

```sql
CREATE UNIQUE INDEX uq_asset_primary_photo
ON attachments (tenant_id, entity_id)
WHERE entity_type = 'ASSET'
  AND attachment_category = 'ASSET_PROFILE_PHOTO'
  AND is_primary = TRUE
  AND deleted_at IS NULL;
```

`assets.primary_photo_attachment_id` boleh ditambahkan sebagai cache untuk
mempercepat list/dashboard. Nilainya harus menunjuk attachment kategori
`ASSET_PROFILE_PHOTO` milik aset yang sama. Sumber kebenaran tetap tabel
`attachments`.

## 38.7 Manual book dan user guide

Manual tidak selalu khusus untuk satu unit aset. Dokumen dapat dilekatkan pada:

- satu aset tertentu;
- asset category;
- model/tipe produk aset;
- manufacturer;
- maintenance plan atau work order tertentu.

Karena itu registry `entity_type` juga dapat diperluas dengan
`ASSET_CATEGORY`, `ASSET_MODEL`, dan `BUSINESS_PARTNER`. Satu `file_id` dapat
memiliki beberapa record `attachments`, sehingga satu manual book dapat
digunakan oleh ratusan aset sejenis tanpa menggandakan binary.

Urutan pencarian dokumen untuk detail aset:

```text
dokumen khusus asset
→ dokumen asset model
→ dokumen asset category
→ dokumen manufacturer
```

Metadata dokumen teknis yang disarankan:

```json
{
  "document_number": "UG-PUMP-X100",
  "revision": "03",
  "language": "id",
  "manufacturer_model": "X100",
  "effective_date": "2026-07-01",
  "page_count": 84
}
```

## 38.8 Lampiran pemeliharaan

Foto pemeliharaan harus terkait dengan record yang paling spesifik:

| Konteks | Entity | Kategori |
|---|---|---|
| Kondisi awal pekerjaan | `MAINTENANCE_WORK_ORDER` | `BEFORE_MAINTENANCE_PHOTO` |
| Proses pengerjaan | `MAINTENANCE_EXECUTION` | `DURING_MAINTENANCE_PHOTO` |
| Hasil akhir | `MAINTENANCE_WORK_ORDER` | `AFTER_MAINTENANCE_PHOTO` |
| Laporan teknisi/vendor | `MAINTENANCE_WORK_ORDER` | `MAINTENANCE_REPORT` |
| Temuan checklist | `MAINTENANCE_FINDING` | `FINDING_PHOTO` |
| Part yang diganti | `PART_REPLACEMENT` | `REPLACED_PART_PHOTO` |

Konfigurasi template/work order dapat menentukan bukti wajib:

```text
require_before_photo
require_after_photo
min_before_photo_count
min_after_photo_count
require_maintenance_report
require_vendor_certificate
```

Work order tidak boleh masuk status `COMPLETED` atau `VERIFIED` bila attachment
wajib belum tersedia dan berstatus antivirus selain `CLEAN`.

## 38.9 Lampiran laporan kerusakan dan failure

Pelapor dapat mengunggah foto saat membuat `maintenance_request`. Setelah
triage, bukti yang menjelaskan failure teknis dapat dilekatkan ke
`asset_failures` tanpa menyalin file:

```text
maintenance_request
    └── attachments: DAMAGE_PHOTO

asset_failure
    └── attachments: FAILURE_PHOTO / ROOT_CAUSE_EVIDENCE
```

Satu `file_id` dapat mempunyai dua attachment links bila foto yang sama memang
relevan pada request dan failure. Relasi asal harus tetap dapat ditelusuri:

```text
asset_failure.maintenance_request_id
asset_failure.work_order_id
```

Foto failure sebaiknya merekam:

- waktu pengambilan;
- pengambil/pelapor;
- asset dan lokasi;
- posisi GPS bila diambil dari perangkat mobile;
- kondisi operasi ketika failure terjadi;
- deskripsi kerusakan;
- tingkat sensitivitas;
- checksum untuk menjaga integritas bukti.

EXIF GPS tidak boleh langsung dipercaya. Backend mengambil metadata, tetapi
nilai lokasi resmi harus divalidasi terhadap izin pengguna dan kebijakan
privasi. Metadata sensitif dapat dihapus dari derivative image yang ditampilkan.

## 38.10 Annotation foto

Untuk menandai area retak, bocor, aus, terbakar, atau komponen yang bermasalah:

```sql
attachment_annotations
----------------------
id UUID PK
attachment_id UUID FK NOT NULL
annotation_type VARCHAR(20) NOT NULL
label VARCHAR(100) NULL
geometry JSONB NOT NULL
notes TEXT NULL
created_by UUID FK NOT NULL
created_at TIMESTAMPTZ NOT NULL
```

`geometry` menggunakan koordinat ternormalisasi 0–1 agar penandaan tetap benar
meskipun gambar ditampilkan dalam ukuran berbeda:

```json
{
  "type": "rectangle",
  "x": 0.21,
  "y": 0.34,
  "width": 0.18,
  "height": 0.12
}
```

## 38.11 Upload dan processing pipeline

```text
request upload session
→ validasi permission, entity, kategori, ukuran, dan MIME
→ upload langsung ke object storage privat
→ finalize dengan checksum
→ antivirus scan
→ ekstraksi metadata
→ image orientation normalization
→ thumbnail/preview generation
→ attachment menjadi AVAILABLE
→ audit event
```

Untuk file besar, API tidak menerima seluruh binary melalui worker FastAPI.
Service menghasilkan short-lived presigned upload URL. Endpoint finalize baru
boleh membuat attachment setelah object key, ukuran, checksum, dan ownership
upload session tervalidasi.

Status pemrosesan:

```text
UPLOADING
PROCESSING
AVAILABLE
QUARANTINED
FAILED
DELETED
```

File `QUARANTINED` tidak boleh diunduh atau dipreview oleh pengguna biasa.

## 38.12 Validasi keamanan file

Validasi wajib:

- allowlist MIME type dan extension;
- cocokkan extension, declared MIME, dan file signature/magic bytes;
- batas ukuran per kategori;
- batas jumlah file per request;
- filename disanitasi dan tidak digunakan sebagai storage object key;
- object key dibuat server menggunakan UUID;
- antivirus/malware scan sebelum file tersedia;
- blok executable, script, macro berbahaya, dan archive yang tidak diperlukan;
- gambar didekode ulang untuk menurunkan risiko payload tersembunyi;
- PDF dipreview melalui derivative, bukan inline raw file tanpa kebijakan;
- download menggunakan signed URL berumur pendek;
- object storage tidak public;
- authorization diperiksa kembali saat download, bukan hanya saat upload;
- seluruh upload, download, version change, dan delete masuk audit log.

Contoh baseline batas ukuran:

| Jenis | MIME | Maksimum |
|---|---|---:|
| Foto | JPEG, PNG, WebP, HEIC bila didukung | 20 MB |
| Dokumen | PDF | 50 MB |
| Office | DOCX, XLSX | 50 MB |
| Video bukti | MP4 | 200 MB |

Nilai tersebut dikonfigurasi melalui environment dan kebijakan tenant.

## 38.13 Authorization dan retention

Permission minimum:

```text
attachment:read
attachment:upload
attachment:update_metadata
attachment:replace_version
attachment:delete
attachment:restore
attachment:download_sensitive
```

Hak akses file mewarisi scope entity:

- pengguna yang dapat melihat asset belum tentu dapat melihat dokumen finansial;
- teknisi dapat melihat manual dan foto maintenance;
- procurement/finance dapat melihat invoice;
- HR atau admin mengendalikan bukti yang memuat data personal;
- vendor hanya dapat mengakses work order dan attachment yang secara eksplisit
  dibagikan.

`visibility`:

```text
INTERNAL
RESTRICTED
VENDOR_SHARED
PUBLIC_REFERENCE
```

Delete dilakukan secara soft delete. Penghapusan object fisik dijalankan
setelah retention period, legal hold, audit, dan seluruh attachment link
diperiksa. File tidak boleh dihapus fisik bila masih digunakan entity lain.

## 38.14 Transaction boundary

Pembuatan attachment:

```text
1. verifikasi upload session dan scan CLEAN;
2. lock entity target bila diperlukan;
3. validasi entity, tenant, permission, dan category;
4. insert/update files;
5. insert attachments;
6. bila primary photo, nonaktifkan primary lama;
7. insert audit log;
8. commit;
9. publish event ATTACHMENT_CREATED melalui outbox.
```

Binary yang sudah terunggah tetapi finalize database gagal ditandai sebagai
orphan dan dibersihkan oleh scheduled job setelah grace period.

## 38.15 Endpoint FastAPI

```text
POST   /api/v1/uploads/sessions
POST   /api/v1/uploads/{upload_session_id}/finalize

POST   /api/v1/attachments
GET    /api/v1/attachments/{attachment_id}
PATCH  /api/v1/attachments/{attachment_id}
DELETE /api/v1/attachments/{attachment_id}
POST   /api/v1/attachments/{attachment_id}/restore
POST   /api/v1/attachments/{attachment_id}/versions
GET    /api/v1/attachments/{attachment_id}/download
GET    /api/v1/attachments/{attachment_id}/preview

GET    /api/v1/assets/{asset_id}/attachments
POST   /api/v1/assets/{asset_id}/attachments
GET    /api/v1/assets/{asset_id}/photos
POST   /api/v1/assets/{asset_id}/primary-photo/{attachment_id}
GET    /api/v1/assets/{asset_id}/manuals

POST   /api/v1/maintenance-requests/{request_id}/attachments
GET    /api/v1/maintenance-requests/{request_id}/attachments
POST   /api/v1/maintenance-work-orders/{work_order_id}/attachments
GET    /api/v1/maintenance-work-orders/{work_order_id}/attachments
POST   /api/v1/failures/{failure_id}/attachments
GET    /api/v1/failures/{failure_id}/attachments
POST   /api/v1/maintenance-findings/{finding_id}/attachments
```

Endpoint domain memanggil `attachments` service. Domain lain tidak menulis
langsung ke repository attachment.

## 38.16 Struktur modul FastAPI

```text
app/modules/attachments/
├── __init__.py
├── constants.py
├── exceptions.py
├── models/
│   ├── file.py
│   ├── file_version.py
│   ├── attachment.py
│   ├── annotation.py
│   └── upload_session.py
├── schemas/
│   ├── upload_session.py
│   ├── attachment_create.py
│   ├── attachment_read.py
│   ├── attachment_filter.py
│   └── annotation.py
├── repositories/
│   ├── file_repository.py
│   ├── attachment_repository.py
│   └── upload_session_repository.py
├── services/
│   ├── attachment_service.py
│   ├── upload_service.py
│   ├── download_service.py
│   ├── image_processing_service.py
│   └── retention_service.py
├── storage/
│   ├── base.py
│   └── s3.py
├── policies/
│   └── attachment_policy.py
├── routes/
│   ├── attachments.py
│   └── uploads.py
└── tests/
    ├── unit/
    └── integration/
```

Antarmuka storage harus independen dari vendor agar MinIO/S3 dapat diganti
tanpa mengubah business service.

## 38.17 Dependency tambahan

Dependency yang dapat ditambahkan ke `requirements_asset_management_fastapi.txt`
ketika fitur attachment diimplementasikan:

```text
boto3
python-magic
Pillow
filetype
clamd
```

`pillow-heif` hanya diperlukan bila aplikasi menerima HEIC/HEIF. Antivirus
engine ClamAV berjalan sebagai service/container terpisah; package Python hanya
menjadi client. Versi harus dipin setelah compatibility test pada Python dan
OS deployment.

## 38.18 Pelaporan

Laporan minimum:

- aset tanpa foto utama;
- aset tanpa manual/dokumen wajib;
- attachment per aset, kategori, lokasi, dan periode;
- work order yang tidak memiliki bukti sebelum/sesudah;
- failure tanpa foto atau root cause evidence;
- file quarantined atau gagal diproses;
- file orphan;
- dokumen yang akan berakhir masa berlaku;
- versi manual/SOP yang masih digunakan tetapi sudah obsolete;
- storage usage per tenant dan kategori.

## 38.19 Definition of Done attachment

- asset dapat memiliki banyak foto dan tepat satu foto utama aktif;
- manual book dan user guide dapat diunggah, dibuat versi baru, dan digunakan
  oleh banyak aset/model;
- maintenance request dapat menyertakan foto kerusakan;
- work order menyimpan foto sebelum, proses, sesudah, dan laporan;
- failure dan checklist finding dapat memiliki bukti foto sendiri;
- part replacement dapat menyimpan foto part lama dan baru;
- attachment tetap traceable ke pelapor, waktu, lokasi, dan entity asal;
- file tidak public dan download selalu melalui authorization;
- MIME, signature, ukuran, checksum, malware, dan tenant tervalidasi;
- file yang belum `CLEAN` tidak dapat digunakan untuk memenuhi bukti wajib;
- soft delete, retention, restore, dan audit trail teruji;
- upload retry bersifat idempotent;
- orphan cleanup dan storage reconciliation tersedia;
- seluruh endpoint mengikuti JSON response baku;
- Alembic migration, unit test, integration test, dan authorization test lulus.
