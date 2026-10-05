# Strict PQC service record integrity

ML-DSA-65 signing and pinned-key verification cover ProductStore resource payloads,
local decisions, Studio, laboratory records, claims, evidence, graphs and quantitative artifacts.
Configure `PRAXIS_PQC_KEY_FILE` with an external JSON key file containing `key_id`,
base64 `public_key` and base64 `secret_key`. Restrict access to the service account.
Do not commit keys. Without this setting, unsigned development records remain supported;
signed records cannot be read without a verifier. Strict configured mode rejects unsigned records.
Keep `PRAXIS_PQC_ALLOW_LEGACY` unset for strict operation.

Stop the application and every writer before local migration:

```powershell
python -m praxis.security.migrate praxis.db --backup private-backups/pre-pqc.db
```

The command refuses to overwrite a backup, snapshots SQLite before modification,
signs supported legacy records in one transaction and verifies the resulting records
before committing. Existing invalid signatures abort the transaction. Migration attests
to the imported snapshot, not historical authorship. Preserve the backup and key securely.
ProductStore databases require a separate migration before activating strict mode;
this local SQLite migrator does not handle product resource tables.

This is record integrity, not complete project security: TLS/PQC channel negotiation,
database encryption, external identity and certificate management, key rotation/HSM,
audit/outbox integrity, static assets, rollback protection and production deployment
remain separate work. Record signatures do not prove physical sensor truth or prevent deletion.
The library is not claimed to be FIPS validated.
