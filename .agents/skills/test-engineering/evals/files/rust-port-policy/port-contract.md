# Port-normalization contract

Status: designated as governing behavior for this exercise by the command-line product owner.

The crate must expose `pub fn normalize_port(value: u32) -> Result<u16, PortError>`.

- Values from 1 through 65,535 return the same value as `u16`.
- Zero returns `Err(PortError::Zero)`.
- Values above 65,535 return `Err(PortError::TooLarge)`.
- `PortError` remains public, comparable with `assert_eq!`, and limited to the existing variants.

The function must be deterministic, side-effect free, dependency free, and constant time.
