# Executable PQC technology lab

This optional Python module performs real cryptographic operations through pinned
PQCrypto 1.0.0. It supports ML-KEM-512/768/1024, ML-DSA-44/65/87 and
SLH-DSA-SHA2-128f. Explicit algorithm selection never silently falls back.

These families correspond to [FIPS 203/204/205](https://csrc.nist.gov/News/2024/postquantum-cryptography-fips-approved).
The dependency's [API documentation](https://pypi.org/project/pqcrypto/1.0.0/)
describes key generation, encapsulation/decapsulation and signature verification.
Standards-based algorithm names do not mean this application or dependency is a
FIPS-validated cryptographic module.

## Run

From the project directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[pqc]"
.\.venv\Scripts\python.exe -m praxis.security.pqc
.\.venv\Scripts\python.exe -m praxis.security.pqc --kem ML-KEM-1024 --signature SLH-DSA-SHA2-128f
```

The installed entry point is `praxis-pqc`. The lab generates ephemeral keys,
compares shared secrets, checks modified ciphertext behavior and verifies valid,
modified-message and wrong-context signatures. Only booleans, public artifact
sizes and local timings appear in its JSON output. Private keys and shared secrets
are not exported. Timings cover multiple operations in a single local trial and
are not aviation or maritime performance benchmarks.

Python developers can import `generate_keys`, `encapsulate`, `decapsulate`, `sign`
and `verify` from `praxis.security.pqc`. Keys and artifacts are bytes. Signatures
use the FIPS context `PRAXIS-PQC-LAB-v1` by default; verification must use the same
context. Verification returns false for invalid signatures/malformed artifacts;
unsupported algorithm choices raise errors.

## Integration limits

ML-KEM establishes a secret; it does not encrypt an arbitrary message or
authenticate the peer. A complete channel needs reviewed identity binding,
transcript/replay handling, key derivation and authenticated symmetric encryption.
This module does not introduce a custom transport construction. Signatures verify
against a supplied key; key enrollment, revocation and identity mapping are not
implemented. No private-key store, HSM/KMS integration, guaranteed memory erasure,
TLS replacement, live flight links or production deployment is provided.

The local tests exercise round trips and negative cases, not published conformance
vectors, external interoperability or side-channel evaluation. Target integration
requires library provenance/assurance review, known-answer vectors, protocol
interoperability and representative-device tests. PQC tests skip if the optional
dependency is absent; install the extra to execute them.
