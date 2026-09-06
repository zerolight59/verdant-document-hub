# Moving Verdant Employees from MySQL to PostgreSQL

Verdant now uses one PostgreSQL database as its authoritative datastore. It does not connect to the Calibration database. The PostgreSQL `employees` table owns Verdant usernames, employee IDs, password hashes, roles, and employee profile information.

This guide covers migration of the existing **Verdant employee table**. Do not run it against a production database without a tested backup and a maintenance window.

## 1. Understand the migration boundary

The repository knows these employee fields:

| PostgreSQL column | Purpose |
|---|---|
| `id` | Stable internal numeric ID; optional in the CSV import. |
| `employee_code` | Company employee ID used for login and assignments. |
| `username` | Optional Verdant username; can also be used to sign in. |
| `name` | Display name. |
| `email` | Unique company email address. |
| `password_hash` | Existing password hash. Plain-text passwords must never be exported. |
| `job_title` | Employee title. |
| `department` | Optional department. |
| `profile_data` | Optional JSON object for additional company-specific fields. |
| `is_admin` | Whether the employee is a Verdant administrator/senior approver. |
| `is_active` | Whether login is enabled. |

If the current MySQL table uses different names or contains additional columns, map the known fields explicitly and place non-authoritative extra profile fields in `profile_data`. Add first-class PostgreSQL columns through Alembic when a field will be searched, validated, joined, or used for authorization.

## 2. Check password-hash compatibility

The current Verdant authentication code writes Argon2 hashes. Existing hashes can be copied only if the Python password library can verify their algorithm.

- Never export or import plain-text passwords.
- Test at least one migrated non-administrator account before allowing general access.
- If the old application uses an incompatible hash, plan a password-reset process. Do not give every employee one shared password.
- Keep the original MySQL database read-only until the migration is accepted.

## 3. Create a CSV export

Create a UTF-8 CSV with this header:

```csv
id,employee_code,username,name,email,password_hash,job_title,department,profile_data,is_admin,is_active
```

`id`, `username`, `job_title`, `department`, and `profile_data` may be blank. Required values are `employee_code`, `name`, `email`, and `password_hash`.

An example MySQL query is shown below. Adjust table and column names to match the existing Verdant database:

```sql
SELECT
    employee_id AS id,
    employee_code,
    username,
    employee_name AS name,
    email,
    password_hash,
    job_title,
    department,
    JSON_OBJECT() AS profile_data,
    is_admin,
    is_active
FROM employee;
```

Use MySQL Workbench’s result export to save the query output as UTF-8 CSV. Store the export in an access-controlled temporary location and delete it securely after acceptance because it contains password hashes and employee information.

## 4. Prepare PostgreSQL first

Follow [Local Windows Installation](LOCAL_INSTALLATION_WINDOWS.md) through the Alembic migration step. Do not run the demo seed when importing real employees.

Confirm that `backend/.env` points to the new PostgreSQL Verdant database. From `backend`:

```powershell
.\.venv\Scripts\alembic.exe current
```

The current revision should be `0001_postgresql`.

## 5. Validate without writing

Place the CSV outside the repository and run:

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\python.exe -m scripts.import_employees_csv C:\SecureTransfer\verdant-employees.csv --dry-run
```

The dry run validates required columns and field formats, then rolls back.

## 6. Import the employees

After reviewing the dry-run count:

```powershell
.\.venv\Scripts\python.exe -m scripts.import_employees_csv C:\SecureTransfer\verdant-employees.csv
```

The importer matches existing PostgreSQL employees by `employee_code`. It inserts new records and updates matching records. When source IDs are supplied for new employees, the PostgreSQL sequence is advanced after import.

## 7. Acceptance checks

Before switching users to PostgreSQL:

1. Compare employee counts and a sample of IDs, usernames, email addresses, titles, departments, administrator flags, and active flags.
2. Sign in with one ordinary employee, one project owner, one reviewer, and one administrator.
3. Confirm inactive employees cannot sign in.
4. Create a test project and verify assignments use the correct employee records.
5. Keep a record of the source export date, row count, migration command, and acceptance result.
6. Remove the CSV from the temporary location after acceptance under company data-handling policy.

## Moving existing project/document data

The included importer intentionally handles only employees. Moving existing MySQL projects, versions, reviews, research, audit history, and file paths requires a separately reviewed migration because table order, foreign keys, stored file locations, IDs, and historical integrity must be preserved together.

Do not run the PostgreSQL Alembic baseline against the old MySQL database. Do not copy tables independently when they contain foreign-key relationships.

## Future pgvector work

PostgreSQL is now the product database, but this baseline does not require the `vector` extension. When content extraction, chunking, and embeddings are implemented:

1. Install pgvector on the PostgreSQL server.
2. Add `CREATE EXTENSION IF NOT EXISTS vector` in a new Alembic migration.
3. Add append-only document-chunk and embedding tables tied to immutable document-version IDs.
4. Store the embedding model name, dimensions, content hash, extraction status, and timestamps.
5. Keep PostgreSQL/document storage as the source of truth; embeddings are derived data that can be regenerated.

Deferring the extension avoids complicating today’s Docker-free Windows installation while preserving the correct future migration path.
