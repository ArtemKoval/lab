# ADR review: add-loop-admission-gate

ADR review completed for this change. No new ADR. The admission gate is
behavior the capability spec carries: the refused state, the shipped
allowed-author list, and the status config row are scan and status
contracts, not durable architecture. The in-force authority record
stays ADR 0013, and the gate narrows the intake the authority grant
serves.
