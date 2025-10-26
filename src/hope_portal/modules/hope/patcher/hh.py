from hope_portal.modules.hope.models import Household, Individual, Individualroleinhousehold

ROLE_PRIMARY = "PRIMARY"
ROLE_ALTERNATE = "ALTERNATE"
ROLE_NO_ROLE = "NO_ROLE"


def get_primary_collector(s: Household) -> Individual | None:
    if e := Individualroleinhousehold.objects.filter(role=ROLE_PRIMARY, household=s).first():
        return e.individual
    return None


Household.primary_collector = property(get_primary_collector)
