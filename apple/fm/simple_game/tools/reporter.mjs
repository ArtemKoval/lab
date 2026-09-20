// tools/reporter.mjs - the machine readable reporter of the unit gate.
//
// The spec reporter of node prints the value of a failed assertion through
// util.inspect. That printer stops at the depth 2, so a nested cell becomes the
// text [Object], and it breaks a long value over many lines. A parser of that text
// loses the one number that the repair prompt needs.
//
// This reporter reads the event stream instead. The event test:fail carries
// details.error.cause.actual and details.error.cause.expected as real values, with
// no depth limit. It prints one line for each failed test, in the format D of the
// build:
//
//   TEST <name> | FILE <path>:<line>:<column> | GOT <json> | EXPECTED <json>
//
// A test that throws an error of another kind prints the message in the GOT field
// and prints no EXPECTED field.

import { relative } from 'node:path';

const ROOT = process.cwd();

function asText(value) {
  try {
    const text = JSON.stringify(value);
    return text === undefined ? String(value) : text;
  } catch {
    return String(value);
  }
}

function oneLine(text) {
  return String(text).replace(/[\r\n\t]+/g, ' ').replace(/ {2,}/g, ' ').trim();
}

export default async function* reporter(source) {
  for await (const event of source) {
    if (event.type !== 'test:fail') { continue; }
    const data = event.data;
    const error = data.details && data.details.error;
    const cause = error && error.cause;
    const file = data.file ? relative(ROOT, data.file) : 'unknown';
    const where = file + ':' + (data.line || 0) + ':' + (data.column || 0);
    const name = oneLine(data.name || 'unnamed');
    if (cause && cause.code === 'ERR_ASSERTION') {
      yield 'TEST ' + name + ' | FILE ' + where +
        ' | GOT ' + oneLine(asText(cause.actual)) +
        ' | EXPECTED ' + oneLine(asText(cause.expected)) + '\n';
      continue;
    }
    const message = (cause && cause.message) || (error && error.message) || 'the test failed';
    yield 'TEST ' + name + ' | FILE ' + where + ' | GOT ' + oneLine(message) + '\n';
  }
}
