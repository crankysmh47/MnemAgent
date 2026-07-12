# Add bounded retry configuration

Add `RETRY_LIMIT` configuration with default `3`. Reject zero, negative, decimal, and non-numeric values. Keep the validation dependency-free and add tests. Touch only `src/config.js` and its tests.

After the first implementation, reviewer feedback establishes that this repository uses `RETRY_LIMIT` and small pure validation functions.
