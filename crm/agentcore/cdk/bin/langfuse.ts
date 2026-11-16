#!/usr/bin/env node
// The Langfuse app: one stack with the self-hosted server. The agentcore
// CLI owns bin/cdk.ts; this app deploys and destroys on its own, with
// `npm run cdk:langfuse` from agentcore/cdk/.
import { App } from 'aws-cdk-lib';
import { LangfuseStack } from '../lib/langfuse-stack';

const app = new App();

// The init values travel as CDK context, so they land in no tracked file:
// npm run cdk:langfuse -- deploy -c langfuse_org=crm -c langfuse_project=crm
//   -c langfuse_user_email=... -c langfuse_user_password=...
//   -c langfuse_public_key=pk-lf-... -c langfuse_secret_key=sk-lf-...
// After the first deploy prints LangfuseHost, deploy again with
//   -c langfuse_host=<LangfuseHost>
// so NEXTAUTH_URL points at the public address.
const userEmail = app.node.tryGetContext('langfuse_user_email') ?? '';
const userPassword = app.node.tryGetContext('langfuse_user_password') ?? '';
const publicKey = app.node.tryGetContext('langfuse_public_key') ?? '';
const secretKey = app.node.tryGetContext('langfuse_secret_key') ?? '';
const missing = Object.entries({ userEmail, userPassword, publicKey, secretKey })
  .filter(([, value]) => !value)
  .map(([name]) => name);
if (missing.length > 0) {
  console.error(
    `Missing CDK context for the init values: ${missing.join(', ')}. ` +
      'Pass every -c langfuse_* flag the rollout skill names.',
  );
  process.exit(1);
}

new LangfuseStack(app, 'LangfuseStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  init: {
    org: app.node.tryGetContext('langfuse_org') ?? 'crm',
    project: app.node.tryGetContext('langfuse_project') ?? 'crm',
    userEmail,
    userPassword,
    publicKey,
    secretKey,
  },
  publicHost: app.node.tryGetContext('langfuse_host') || undefined,
});

app.synth();
