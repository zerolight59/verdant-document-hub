from app.models import Base


def test_product_schema_contains_core_domains():
    expected_tables = {
        "employees",
        "projects",
        "project_members",
        "document_requirements",
        "document_versions",
        "document_reviews",
        "research_documents",
        "research_document_versions",
        "audit_logs",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_employee_and_audit_product_fields_are_present():
    employees = Base.metadata.tables["employees"]
    audit_logs = Base.metadata.tables["audit_logs"]

    assert {"employee_code", "username", "department", "profile_data"} <= set(
        employees.columns.keys()
    )
    assert "project_id" in audit_logs.columns
