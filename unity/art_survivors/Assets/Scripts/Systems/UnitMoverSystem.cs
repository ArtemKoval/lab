using Authoring;
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Physics;
using Unity.Transforms;

namespace Systems {
	public partial struct UnitMoverSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var unitMoverJob = new UnitMoverJob {
				deltaTime = SystemAPI.Time.DeltaTime
			};
			unitMoverJob.ScheduleParallel();
		}
	}
}

[BurstCompile]
public partial struct UnitMoverJob : IJobEntity {
	public float deltaTime;

	public void Execute(
		ref LocalTransform localTransform,
		ref UnitMover unitMover,
		ref PhysicsVelocity physicsVelocity
	) {
		// if (unitMover.IsController
		//     & unitMover.TargetPosition.x == 0
		//     & unitMover.TargetPosition.y == 0) {
		// 	physicsVelocity.Linear = float3.zero;
		// 	physicsVelocity.Angular = float3.zero;
		// 	return;
		// }

		var moveDirection = unitMover.IsController
			? unitMover.TargetPosition
			: unitMover.TargetPosition - localTransform.Position;
		const float reachedTargetDistanceSq = 0.01f;
		if (math.lengthsq(moveDirection) < reachedTargetDistanceSq) {
			physicsVelocity.Linear = float3.zero;
			physicsVelocity.Angular = float3.zero;
			return;
		}

		moveDirection = math.normalizesafe(moveDirection);
		// for 2d use sprite flip instead of rotation todo
		// localTransform.ValueRW.Rotation = quaternion.LookRotation(moveDirection, math.up());
		physicsVelocity.Linear = moveDirection * unitMover.MoveSpeed;
		physicsVelocity.Angular = float3.zero; // freeze rotation on collisions
		// if (unitMover.IsController) unitMover.TargetPosition = new float3();
	}
}