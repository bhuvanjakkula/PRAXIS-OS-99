# Aviation security and technology development

Use Aircrew > Enable aviation coordination review > Add security technology
project. Four scopes cover airports, aircraft, command teams and operations.
Seven security areas cover identity/access, data links, software supply chain,
network isolation, navigation integrity, incident recovery and quantum migration.

Development stages are discovery, prototype, validation and handover. Each project
records its asset/interface, approach, owner, responsible command/operations role,
threat requirements, inventory, authentication/key lifecycle, applicability,
isolated test plan, next action and review date. Validation/handover require
validation, performance/interoperability, fallback/rollback and safety/authority
references. QKD research also requires link and failure evidence. Open findings
remain visible. Stages are supplied requests; the software never advances them
automatically or authorizes deployment. Complete evidence is documented unverified.

Projects save with the existing tenant/revision-bound incident record and handover
export. Missing scopes are shown as coverage information, not mandatory controls.
Existing aviation records without projects remain supported.

## Practical development sequence

1. Inventory the selected assets, links, cryptographic dependencies, suppliers,
   data sensitivity and expected lifetime. Assign accountable owners.
2. Define the intended security properties, failure behavior, compatibility,
   resource limits and applicable safety/change authority.
3. Prototype in an isolated representative environment. Test authentication,
   replay handling, key rotation/revocation, updates and recovery as applicable.
4. Record measured latency, memory/CPU, bandwidth, interoperability, downgrade
   behavior and fault/attack results. Keep unresolved findings visible.
5. Obtain the authorized engineering and operational review before changing
   any real airport, aircraft or command interface outside this application.

## Quantum scope and sources

[NIST's approved standards](https://www.nist.gov/news-events/news/2024/08/announcing-approval-three-federal-information-processing-standards-fips)
identify ML-KEM for key encapsulation and ML-DSA/SLH-DSA for signatures. These are
post-quantum cryptographic primitives, not quantum hardware or aviation
certification. Algorithm selection and integration need an interface-specific
design and reviewed implementation.

[NSA's QKD guidance](https://www.nsa.gov/Cybersecurity/Quantum-Key-Distribution-QKD-and-Quantum-Cryptography-QC/)
describes authentication, hardware, validation and availability limitations in
the National Security Systems context. It is not a civil-aviation mandate.
QKD and PQC are separate approaches in this workbench; QKD proposals must record
authentication and link-failure/fallback evidence.

The supplied summary, attachment `3b86ab4d-0478-47aa-997b-a572ea7aff93`, informed
development themes. Its paper-specific overhead, accuracy, quantum-learning and
operational-protection claims were not adopted as verified product capabilities.

This implementation develops planning and evidence-review software. It does not
encrypt flight links, secure ADS-B broadcasts, implement QKD/PQC, connect airport
or aircraft systems, monitor people, issue commander credentials, change schedules
or grant flight clearance. Real system integration needs selected interfaces,
authorized access, engineering requirements and representative test facilities.
