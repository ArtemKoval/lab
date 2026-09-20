TEMPLATE
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { {{EXPORT_LIST}} } from '{{MODULE_PATH}}';
test('NAME', () => {
  BODY
});

{{FILL_BLOCKS}}

Emit the imports once, then one filled test block for each FILL.
