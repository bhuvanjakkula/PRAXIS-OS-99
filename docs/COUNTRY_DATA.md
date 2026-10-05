# Local individual country data

Country leadership includes one searchable country-data box for 217 World Bank
country and economy entries, plus custom entries. Regional/income aggregates are
excluded. These reporting units are not a sovereignty classification.
Each country has attributed GDP (current USD), population, real GDP growth and
consumer inflation, observation years, up to five recent nonempty observations,
and source update/download dates. The 2026-10-02 snapshot has 838 of 868 available
latest values; 30 missing indicators remain explicitly unavailable. Profiles also
include provider-reported region, income classification and capital metadata.
Indicator years can differ; a download date does not make historical values current.
Country-specific law, institutions and agreements are not inferred.

Data comes from the [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392),
using source 2 and most-recent-nonempty observations. The [query documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581)
explains MRNEV. Attribution and a public-license reference are stored locally.
The downloader retrieves the provider catalog, retains existing country display
names for compatibility, and checks country/indicator identities, finite values, dates and
pagination before replacing the snapshot. Network failures receive at most three
attempts; an incomplete response leaves the previous snapshot in place. No AI
provider or token is used.

src/praxis/web/country-data.json ships in the wheel and release. Running
tools/refresh_country_data.py explicitly downloads a new snapshot; the application
does not periodically contact the provider. Backend saves check the checksum and
snapshot identifier and preserve selected-country statistics with the plan.
The checksum detects content changes but is not a digital signature or protection
against an attacker who can replace both the data and checksum.

The deliberate GDP import fills only a dated baseline scaled to billion USD and
adds a source note. Fiscal projections and nominal growth remain user inputs.
Incompatible monetary units are not overwritten; real growth never populates
nominal growth. A warning identifies assessments dated before the download.
Custom countries without snapshot coverage require supplied sources.

Tests cover country coverage, attribution, history ordering, identity/integrity,
and saved context without invented projections. Browser checks cover search,
individual selection, GDP import, saved snapshot context, appraisal, reloads
and mobile layout.
