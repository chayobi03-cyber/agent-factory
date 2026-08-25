# Generic Engineering Evidence — Runtime Integration RCA and Preventive Controls

## Root cause

The Generic Engineering Evidence Contract and machine-readable schema already existed, but runtime execution did not yet produce the envelope as part of the actual evidence path. The missing link was between a domain payload and a machine-verified execution manifest.

This created a structural risk: a contract could be unit-tested while real CI evidence continued to be represented by separate workflow outputs. The system therefore had no single runtime object proving, in one chain, target/runtime SHA identity, domain-pack identity, provenance, artifact digest, validation disposition, manifest binding, and HOTL state.

## Corrective architecture

The runtime evidence layer is now implemented outside `src/cer_runtime.py` and `src/factory_runtime.py`:

`Domain Pack payload → Generic Evidence Envelope → Manifest hash → Runtime validator → CI artifact`

The Kernel remains domain-neutral. RE/EMI/CST/ESD provide only payload mappings and never require Kernel schema branches.

## Preventive controls

1. **Runtime enforcement, not schema-only validation.** Every CI execution creates and validates the envelope.
2. **Fail-closed identity binding.** `target_sha != runtime_sha` is an immediate failure; evidence cannot become GREEN.
3. **Independent artifact hashing.** The runtime recalculates the payload artifact SHA-256 before validation.
4. **Manifest binding.** Envelope and manifest carry the same deterministic manifest hash.
5. **Cross-domain contract regression.** RE/EMI/CST/ESD must emit the same envelope structure.
6. **Kernel boundary regression.** The generic evidence implementation is kept independent of the Kernel runtime modules.
7. **Evidence-first gate.** Engineering-document ingestion remains downstream of this runtime evidence integration.
8. **Promotion freeze remains absolute.** OPRO promotion, GEPA implementation, and audited-baseline changes remain forbidden until separately governed gates are satisfied.

## Long-term control model

Future Domain Packs should be admitted through one acceptance test:

`new Domain Pack → payload mapping → generic envelope → runtime manifest → digest verification → domain regression`

A new domain therefore changes data and validators, not evidence semantics. This is the intended scalability boundary for Agent Factory.
