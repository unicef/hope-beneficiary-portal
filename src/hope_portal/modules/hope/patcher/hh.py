from hope_portal.modules.hope.models import Household, Individual, Individualroleinhousehold

ROLE_PRIMARY = "PRIMARY"
ROLE_ALTERNATE = "ALTERNATE"
ROLE_NO_ROLE = "NO_ROLE"

RELATIONSHIPS = (
    "Unknown",
    "Aunt / Uncle",
    "Brother / Sister",
    "Cousin",
    "Daughter-in-law / Son-in-law",
    "Granddaughter / Grandson",
    "Grandmother / Grandfather",
    "Mother / Father",
)

RELATIONSHIP_CHOICE = list(zip(RELATIONSHIPS, RELATIONSHIPS, strict=True))


def get_primary_collector(s: Household) -> Individual | None:
    if e := Individualroleinhousehold.objects.filter(role=ROLE_PRIMARY, household=s).first():
        return e.individual
    return None


Household.primary_collector = property(get_primary_collector)

Individual._meta.get_field("relationship").choices = RELATIONSHIP_CHOICE
Individual.get_issue_type_display = lambda s: dict(RELATIONSHIP_CHOICE)[s.issue_type]
