import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import { ApplicationLoadBalancedFargateService } from 'aws-cdk-lib/aws-ecs-patterns';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import { CfnCacheCluster, CfnSubnetGroup } from 'aws-cdk-lib/aws-elasticache';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as servicediscovery from 'aws-cdk-lib/aws-servicediscovery';

export interface LangfuseStackProps extends StackProps {
  /** The init values the server seeds its first boot with, from CDK context. */
  init: {
    org: string;
    project: string;
    userEmail: string;
    userPassword: string;
    publicKey: string;
    secretKey: string;
  };
  /** The public host for NEXTAUTH_URL, set on the deploy after the first. */
  publicHost?: string;
}

// Only hex digits stay in the generated encryption key, and the server reads
// it as a 32-byte hex key.
const HEX_ONLY = 'ghijklmnopqrstuvwxyzghijklmnopqrstuvwxyz';

/**
 * The self-hosted Langfuse server for the crm engine's runtimes: web and
 * worker on ECS Fargate behind one public ALB, with RDS Postgres,
 * ElastiCache Redis, one ClickHouse task on one EBS volume, and S3 for the
 * object store. The agentcore app in this directory stays untouched; this
 * stack deploys and destroys on its own.
 */
export class LangfuseStack extends Stack {
  constructor(scope: Construct, id: string, props: LangfuseStackProps) {
    super(scope, id, props);

    // One VPC with public subnets in two AZs, and no NAT: every task holds a
    // public address, and the security groups hold the traffic in.
    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        { cidrMask: 20, name: 'public', subnetType: ec2.SubnetType.PUBLIC },
      ],
    });

    const objectStore = new s3.Bucket(this, 'ObjectStore', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const nextAuthSecret = new secretsmanager.Secret(this, 'NextAuthSecret', {
      generateSecretString: {},
    });
    const salt = new secretsmanager.Secret(this, 'Salt', {
      generateSecretString: {},
    });
    const encryptionKey = new secretsmanager.Secret(this, 'EncryptionKey', {
      generateSecretString: { passwordLength: 64, excludePunctuation: true, excludeCharacters: HEX_ONLY },
    });
    const clickHousePassword = new secretsmanager.Secret(this, 'ClickHousePassword', {
      generateSecretString: { excludePunctuation: true },
    });

    const postgres = new rds.DatabaseInstance(this, 'Postgres', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_17,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      publiclyAccessible: false,
      multiAz: false,
      deletionProtection: false,
      removalPolicy: RemovalPolicy.DESTROY,
      credentials: rds.Credentials.fromGeneratedSecret('postgres'),
    });

    const redisSg = new ec2.SecurityGroup(this, 'RedisSg', {
      vpc,
      description: 'Ingress to the Langfuse Redis node',
    });
    const redisSubnetGroup = new CfnSubnetGroup(this, 'RedisSubnetGroup', {
      // The stack name keeps the name unique beside any other stack in the
      // region.
      cacheSubnetGroupName: `langfuse-redis-subnets-${this.stackName}`,
      subnetIds: vpc.publicSubnets.map((subnet) => subnet.subnetId),
      description: 'Subnets for the Langfuse Redis node',
    });
    const redis = new CfnCacheCluster(this, 'Redis', {
      engine: 'redis',
      cacheNodeType: 'cache.t4g.micro',
      numCacheNodes: 1,
      cacheSubnetGroupName: redisSubnetGroup.cacheSubnetGroupName,
      vpcSecurityGroupIds: [redisSg.securityGroupId],
    });

    // The services reach each other by name inside the namespace.
    const namespace = new servicediscovery.PrivateDnsNamespace(this, 'Namespace', {
      name: 'crm.local',
      vpc,
    });

    const cluster = new ecs.Cluster(this, 'Cluster', { vpc });

    // The datastore task: one ClickHouse node on the task's own storage. A
    // task replacement starts a fresh store, which the design accepts.
    const datastoreTask = new ecs.FargateTaskDefinition(this, 'DatastoreTask', {
      memoryLimitMiB: 2048,
      cpu: 1024,
      ephemeralStorageGiB: 24,
    });
    const datastoreContainer = datastoreTask.addContainer('ClickHouse', {
      image: ecs.ContainerImage.fromRegistry('docker.io/clickhouse/clickhouse-server:26.3.62.3'),
      environment: {
        CLICKHOUSE_DB: 'default',
        CLICKHOUSE_USER: 'clickhouse',
      },
      secrets: {
        CLICKHOUSE_PASSWORD: ecs.Secret.fromSecretsManager(clickHousePassword),
      },
      logging: ecs.LogDriver.awsLogs({ streamPrefix: 'langfuse-clickhouse' }),
    });
    datastoreContainer.addPortMappings({ containerPort: 8123 }, { containerPort: 9000 });
    const clickHouseSg = new ec2.SecurityGroup(this, 'ClickHouseSg', {
      vpc,
      description: 'Ingress to the Langfuse ClickHouse node',
    });
    new ecs.FargateService(this, 'Datastore', {
      cluster,
      taskDefinition: datastoreTask,
      assignPublicIp: true,
      securityGroups: [clickHouseSg],
      cloudMapOptions: { cloudMapNamespace: namespace, name: 'clickhouse' },
      desiredCount: 1,
    });

    const clickHouseHost = 'clickhouse.crm.local';
    const databaseUrl = `postgresql://postgres:${postgres
      .secret!.secretValueFromJson('password')
      .unsafeUnwrap()}@${postgres.dbInstanceEndpointAddress}:5432/postgres`;

    const sharedEnv: Record<string, string> = {
      NEXTAUTH_URL: props.publicHost ? `http://${props.publicHost}` : 'http://localhost:3000',
      DATABASE_URL: databaseUrl,
      CLICKHOUSE_MIGRATION_URL: `clickhouse://${clickHouseHost}:9000`,
      CLICKHOUSE_URL: `http://${clickHouseHost}:8123`,
      CLICKHOUSE_USER: 'clickhouse',
      LANGFUSE_S3_EVENT_UPLOAD_BUCKET: objectStore.bucketName,
      LANGFUSE_S3_EVENT_UPLOAD_REGION: this.region,
      LANGFUSE_S3_EVENT_UPLOAD_PREFIX: 'events/',
      LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE: 'false',
      LANGFUSE_S3_MEDIA_UPLOAD_BUCKET: objectStore.bucketName,
      LANGFUSE_S3_MEDIA_UPLOAD_REGION: this.region,
      LANGFUSE_S3_MEDIA_UPLOAD_PREFIX: 'media/',
      LANGFUSE_S3_MEDIA_UPLOAD_FORCE_PATH_STYLE: 'false',
      REDIS_HOST: redis.attrConfigurationEndpointAddress,
      REDIS_PORT: '6379',
      TELEMETRY_ENABLED: 'false',
    };
    const sharedSecrets: Record<string, ecs.Secret> = {
      NEXTAUTH_SECRET: ecs.Secret.fromSecretsManager(nextAuthSecret),
      SALT: ecs.Secret.fromSecretsManager(salt),
      ENCRYPTION_KEY: ecs.Secret.fromSecretsManager(encryptionKey),
      CLICKHOUSE_PASSWORD: ecs.Secret.fromSecretsManager(clickHousePassword),
    };

    // The web service holds the trace intake and the UI, behind the ALB.
    const web = new ApplicationLoadBalancedFargateService(this, 'Web', {
      cluster,
      taskImageOptions: {
        image: ecs.ContainerImage.fromRegistry('docker.langfuse.com/langfuse/langfuse:4'),
        containerPort: 3000,
        environment: {
          ...sharedEnv,
          LANGFUSE_INIT_ORG_ID: props.init.org,
          LANGFUSE_INIT_ORG_NAME: props.init.org,
          LANGFUSE_INIT_PROJECT_ID: props.init.project,
          LANGFUSE_INIT_PROJECT_NAME: props.init.project,
          LANGFUSE_INIT_PROJECT_PUBLIC_KEY: props.init.publicKey,
          LANGFUSE_INIT_PROJECT_SECRET_KEY: props.init.secretKey,
          LANGFUSE_INIT_USER_EMAIL: props.init.userEmail,
          LANGFUSE_INIT_USER_PASSWORD: props.init.userPassword,
        },
        secrets: sharedSecrets,
        enableLogging: true,
      },
      taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      publicLoadBalancer: true,
      healthCheckGracePeriod: Duration.seconds(120),
      desiredCount: 1,
    });
    web.targetGroup.configureHealthCheck({
      path: '/api/public/health',
      healthyThresholdCount: 2,
      unhealthyThresholdCount: 5,
      interval: Duration.seconds(15),
      timeout: Duration.seconds(5),
    });

    // The worker drains the queue and writes to ClickHouse and the store.
    const workerTask = new ecs.FargateTaskDefinition(this, 'WorkerTask', {
      memoryLimitMiB: 1024,
      cpu: 512,
    });
    const workerContainer = workerTask.addContainer('Worker', {
      image: ecs.ContainerImage.fromRegistry('docker.langfuse.com/langfuse/langfuse-worker:4'),
      environment: sharedEnv,
      secrets: sharedSecrets,
      logging: ecs.LogDriver.awsLogs({ streamPrefix: 'langfuse-worker' }),
    });
    workerContainer.addPortMappings({ containerPort: 3030 });
    const workerSg = new ec2.SecurityGroup(this, 'WorkerSg', {
      vpc,
      description: 'Ingress to the Langfuse worker',
    });
    new ecs.FargateService(this, 'Worker', {
      cluster,
      taskDefinition: workerTask,
      assignPublicIp: true,
      securityGroups: [workerSg],
      desiredCount: 1,
    });

    // The task roles reach the object store with no static keys.
    objectStore.grantReadWrite(web.taskDefinition.taskRole);
    workerTask.taskRole.attachInlinePolicy(
      new iam.Policy(this, 'WorkerObjectStore', {
        statements: [
          new iam.PolicyStatement({
            actions: ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
            resources: [objectStore.bucketArn, `${objectStore.bucketArn}/*`],
          }),
        ],
      }),
    );

    // The ALB reaches the web container through the pattern's own rules. The
    // web and the worker reach the datastores, and nothing else comes in.
    const webSg = web.service.connections.securityGroups[0];
    for (const source of [webSg, workerSg]) {
      clickHouseSg.addIngressRule(source, ec2.Port.tcp(8123), 'http queries');
      clickHouseSg.addIngressRule(source, ec2.Port.tcp(9000), 'native queries');
      redisSg.addIngressRule(source, ec2.Port.tcp(6379), 'redis commands');
      postgres.connections.allowDefaultPortFrom(source, 'postgres queries');
    }

    new CfnOutput(this, 'LangfuseHost', {
      value: web.loadBalancer.loadBalancerDnsName,
      description: 'The public address of the Langfuse server',
    });
  }
}
