"""Initial policies are named once; persisted department IDs carry them after renames."""

HOSPITAL_DEPARTMENTS = {"护理部", "医院", "门诊", "办公室"}
MEDICAL_DEPARTMENTS = {"医院", "护理部"}


def initial_report_group(context):
    return (
        "hospital"
        if context.get_current_parameters().get("name") in HOSPITAL_DEPARTMENTS
        else "network"
    )


def initial_medical_access(context):
    return int(context.get_current_parameters().get("name") in MEDICAL_DEPARTMENTS)
