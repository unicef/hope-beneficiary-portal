from django.utils.translation import gettext as _

from hope_portal.modules.hope.models import Grievanceticket

STATUS_NEW = 1
STATUS_ASSIGNED = 2
STATUS_IN_PROGRESS = 3
STATUS_ON_HOLD = 4
STATUS_FOR_APPROVAL = 5
STATUS_CLOSED = 6

CATEGORY_PAYMENT_VERIFICATION = 1
CATEGORY_DATA_CHANGE = 2
CATEGORY_SENSITIVE_GRIEVANCE = 3
CATEGORY_GRIEVANCE_COMPLAINT = 4
CATEGORY_NEGATIVE_FEEDBACK = 5
CATEGORY_REFERRAL = 6
CATEGORY_POSITIVE_FEEDBACK = 7
CATEGORY_NEEDS_ADJUDICATION = 8
CATEGORY_SYSTEM_FLAGGING = 9

ISSUE_TYPE_DATA_BREACH = 1
ISSUE_TYPE_BRIBERY_CORRUPTION_KICKBACK = 2
ISSUE_TYPE_FRAUD_FORGERY = 3
ISSUE_TYPE_FRAUD_MISUSE = 4
ISSUE_TYPE_HARASSMENT = 5
ISSUE_TYPE_INAPPROPRIATE_STAFF_CONDUCT = 6
ISSUE_TYPE_UNAUTHORIZED_USE = 7
ISSUE_TYPE_CONFLICT_OF_INTEREST = 8
ISSUE_TYPE_GROSS_MISMANAGEMENT = 9
ISSUE_TYPE_PERSONAL_DISPUTES = 10
ISSUE_TYPE_SEXUAL_HARASSMENT = 11
ISSUE_TYPE_MISCELLANEOUS = 12

ISSUE_TYPE_HOUSEHOLD_DATA_CHANGE_DATA_UPDATE = 13
ISSUE_TYPE_INDIVIDUAL_DATA_CHANGE_DATA_UPDATE = 14
ISSUE_TYPE_DATA_CHANGE_DELETE_INDIVIDUAL = 15
ISSUE_TYPE_DATA_CHANGE_ADD_INDIVIDUAL = 16
ISSUE_TYPE_DATA_CHANGE_DELETE_HOUSEHOLD = 17

ISSUE_TYPE_PAYMENT_COMPLAINT = 18
ISSUE_TYPE_FSP_COMPLAINT = 19
ISSUE_TYPE_REGISTRATION_COMPLAINT = 20
ISSUE_TYPE_OTHER_COMPLAINT = 21
ISSUE_TYPE_PARTNER_COMPLAINT = 22

ISSUE_TYPE_UNIQUE_IDENTIFIERS_SIMILARITY = 23
ISSUE_TYPE_BIOGRAPHICAL_DATA_SIMILARITY = 24
ISSUE_TYPE_BIOMETRICS_SIMILARITY = 25

ISSUE_TYPES_CHOICES = {
    CATEGORY_DATA_CHANGE: {
        ISSUE_TYPE_DATA_CHANGE_ADD_INDIVIDUAL: _("Add Individual"),
        ISSUE_TYPE_HOUSEHOLD_DATA_CHANGE_DATA_UPDATE: _("Household Data Update"),
        ISSUE_TYPE_INDIVIDUAL_DATA_CHANGE_DATA_UPDATE: _("Individual Data Update"),
        ISSUE_TYPE_DATA_CHANGE_DELETE_INDIVIDUAL: _("Withdraw Individual"),
        ISSUE_TYPE_DATA_CHANGE_DELETE_HOUSEHOLD: _("Withdraw Household"),
    },
    CATEGORY_SENSITIVE_GRIEVANCE: {
        ISSUE_TYPE_BRIBERY_CORRUPTION_KICKBACK: _("Bribery, corruption or kickback"),
        ISSUE_TYPE_DATA_BREACH: _("Data breach"),
        ISSUE_TYPE_CONFLICT_OF_INTEREST: _("Conflict of interest"),
        ISSUE_TYPE_FRAUD_FORGERY: _("Fraud and forgery"),
        ISSUE_TYPE_FRAUD_MISUSE: _("Fraud involving misuse of programme funds by third party"),
        ISSUE_TYPE_GROSS_MISMANAGEMENT: _("Gross mismanagement"),
        ISSUE_TYPE_HARASSMENT: _("Harassment and abuse of authority"),
        ISSUE_TYPE_INAPPROPRIATE_STAFF_CONDUCT: _("Inappropriate staff conduct"),
        ISSUE_TYPE_MISCELLANEOUS: _("Miscellaneous"),
        ISSUE_TYPE_PERSONAL_DISPUTES: _("Personal disputes"),
        ISSUE_TYPE_SEXUAL_HARASSMENT: _("Sexual harassment and sexual exploitation"),
        ISSUE_TYPE_UNAUTHORIZED_USE: _("Unauthorized use, misuse or waste of UNICEF property or funds"),
    },
    CATEGORY_GRIEVANCE_COMPLAINT: {
        ISSUE_TYPE_PAYMENT_COMPLAINT: _("Payment Related Complaint"),
        ISSUE_TYPE_FSP_COMPLAINT: _("FSP Related Complaint"),
        ISSUE_TYPE_REGISTRATION_COMPLAINT: _("Registration Related Complaint"),
        ISSUE_TYPE_OTHER_COMPLAINT: _("Other Complaint"),
        ISSUE_TYPE_PARTNER_COMPLAINT: _("Partner Related Complaint"),
    },
    CATEGORY_NEEDS_ADJUDICATION: {
        ISSUE_TYPE_UNIQUE_IDENTIFIERS_SIMILARITY: _("Unique Identifiers Similarity"),
        ISSUE_TYPE_BIOGRAPHICAL_DATA_SIMILARITY: _("Biographical Data Similarity"),
        ISSUE_TYPE_BIOMETRICS_SIMILARITY: _("Biometrics Similarity"),
    },
}
ALL_ISSUE_TYPES = [choice for choices_group in ISSUE_TYPES_CHOICES.values() for choice in choices_group.items()]
STATUS_CHOICES = (
    (STATUS_NEW, _("New")),
    (STATUS_ASSIGNED, _("Assigned")),
    (STATUS_CLOSED, _("Closed")),
    (STATUS_FOR_APPROVAL, _("For Approval")),
    (STATUS_IN_PROGRESS, _("In Progress")),
    (STATUS_ON_HOLD, _("On Hold")),
)

MANUAL_CATEGORIES = (
    (CATEGORY_DATA_CHANGE, _("Data Change")),
    (CATEGORY_GRIEVANCE_COMPLAINT, _("Grievance Complaint")),
    (CATEGORY_NEGATIVE_FEEDBACK, _("Negative Feedback")),
    (CATEGORY_POSITIVE_FEEDBACK, _("Positive Feedback")),
    (CATEGORY_REFERRAL, _("Referral")),
    (CATEGORY_SENSITIVE_GRIEVANCE, _("Sensitive Grievance")),
)
SYSTEM_CATEGORIES = (
    (CATEGORY_NEEDS_ADJUDICATION, _("Needs Adjudication")),
    (CATEGORY_PAYMENT_VERIFICATION, _("Payment Verification")),
    (CATEGORY_SYSTEM_FLAGGING, _("System Flagging")),
)
CATEGORY_CHOICES = SYSTEM_CATEGORIES + MANUAL_CATEGORIES

CREATE_CATEGORY_CHOICES = (
    (CATEGORY_DATA_CHANGE, _("Data Change")),
    (CATEGORY_GRIEVANCE_COMPLAINT, _("Grievance Complaint")),
    (CATEGORY_REFERRAL, _("Referral")),
    (CATEGORY_SENSITIVE_GRIEVANCE, _("Sensitive Grievance")),
)

SEARCH_TICKET_TYPES_LOOKUPS = {
    "complaint_ticket_details": {
        "individual": "individual",
        "household": "household",
        "payment_record": "payment_record",
    },
    "sensitive_ticket_details": {
        "individual": "individual",
        "household": "household",
        "payment_record": "payment_record",
    },
    "positive_feedback_ticket_details": {
        "individual": "individual",
        "household": "household",
    },
    "negative_feedback_ticket_details": {
        "individual": "individual",
        "household": "household",
    },
    "referral_ticket_details": {
        "individual": "individual",
        "household": "household",
    },
    "individual_data_update_ticket_details": {
        "individual": "individual",
        "household": "individual__household",
    },
    "add_individual_ticket_details": {
        "household": "household",
    },
    "household_data_update_ticket_details": {
        "household": "household",
    },
    "system_flagging_ticket_details": {
        "golden_records_individual": "golden_records_individual",
    },
    "needs_adjudication_ticket_details": {
        "golden_records_individual": "golden_records_individual",
    },
}

Grievanceticket._meta.get_field("status").choices = STATUS_CHOICES
Grievanceticket.get_status_display = lambda s: dict(STATUS_CHOICES)[s.status]

Grievanceticket._meta.get_field("issue_type").choices = ALL_ISSUE_TYPES
Grievanceticket.get_issue_type_display = lambda s: dict(ALL_ISSUE_TYPES)[s.issue_type]
