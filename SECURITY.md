# Security

## Public-repository security boundary

Arkadia is intentionally public. The repository is a proof surface for architecture, implementation, evidence, and verification. Private operational data and credentials remain outside the public tree.

See [PUBLIC_SURFACE.md](PUBLIC_SURFACE.md) for the publication boundary.

## Historical credential exposure

A historical review identified credential material in earlier public commits. Remediation commits subsequently removed the affected material from the current tree and added repository hygiene for credential artifacts.

The affected credentials must be treated as compromised unless the issuing provider has independently confirmed rotation or revocation. This document does **not** claim that rotation or revocation has been verified.

No secret values are recorded here, in issues, or in review comments.

### Current status

- Current-tree secret-shaped configuration: placeholders and environment references only in the inspected files.
- Historical exposure: **CONFIRMED**.
- Provider-side rotation/revocation: **UNKNOWN until independently evidenced**.
- Full Git object-history scan: **PASSED** on GitHub Actions run 36517612969.
- Public-repository secret scanning: GitHub provides secret scanning for public repositories; repository-level push-protection configuration still requires independent settings verification. 

## Required remediation evidence

For every credential known to have been exposed historically, closure requires:

1. provider-side rotation or revocation evidence;
2. confirmation that the replacement credential is deployment-managed and not committed;
3. a full-history secret scan with no unresolved real-secret findings;
4. a current-tree review showing no private credential material;
5. continued prevention of new leaks through secret scanning/push protection where available.

## Do not rewrite history automatically

Historical architecture and security evidence should remain inspectable. Rewriting Git history is a separate destructive operation and requires explicit authorization after the credential-remediation state is known.

## Reporting

If a new credential exposure is discovered, do not paste the credential into an issue, pull request, commit, or chat. Record only the affected provider/category, location class, remediation state, and evidence reference.
