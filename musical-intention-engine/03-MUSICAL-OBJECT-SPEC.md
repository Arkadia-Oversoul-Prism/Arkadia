# MIE · Musical Object Specification

This is intentionally provisional.

## Required conceptual separation

SOURCE AUDIO
→ MUSICAL REPRESENTATION
→ RENDERED RESULT

A MusicalObject must not collapse those three layers into one opaque blob.

## Initial fields under investigation

- id
- source reference
- source type
- human intention
- audio reference
- musical representation
- detected timing
- detected pitch where applicable
- detected rhythm where applicable
- confidence
- transformation history
- parent/original relationship
- rendering reference
- created timestamp

## Provenance

A transformed object records:

`object_id`, `source_id`, `parent_id`, `transformation`, `parameters`, `result`.

The original must remain recoverable.

## Status

EXPERIMENTAL. The schema must change when evidence shows a better representation.
