# Theme persistence contract

Status: designated as governing behavior for this exercise by the web product owner.

The page supports `light` and `dark` themes. Activating `#theme-toggle` must switch the root element's `data-theme` value and store the selected value under local-storage key `theme`. On a later page load in the same browser profile, initialization must restore that stored theme before the user interacts. Missing or unsupported stored values must produce `light`.

The existing DOM IDs, storage key, and exported function names are compatibility requirements. No new runtime dependency is authorized.
