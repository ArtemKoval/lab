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
			var unitMoverJob = new UnitMoverJob() {
				deltaTime = SystemAPI.Time.DeltaTime
			};
			unitMoverJob.ScheduleParallel();

			// foreach (var (localTransform,
			// 	         unitMover,
			// 	         physicsVelocity)
			//          in SystemAPI.Query<
			// 		         RefRW<LocalTransform>,
			// 		         RefRO<UnitMover>,
			// 		         RefRW<PhysicsVelocity>>
			// 	         ()) {
			// 	var moveDirection = unitMover.ValueRO.TargetPosition - localTransform.ValueRO.Position;
			// 	moveDirection = math.normalizesafe(moveDirection);
			//
			// 	// for 2d use sprite flip instead of rotation todo
			// 	// localTransform.ValueRW.Rotation = quaternion.LookRotation(moveDirection, math.up());
			//
			// 	physicsVelocity.ValueRW.Linear = moveDirection * unitMover.ValueRO.MoveSpeed;
			// 	physicsVelocity.ValueRW.Angular = float3.zero; // freeze rotation on collisions
			// }
		}
	}
}

[BurstCompile]
public partial struct UnitMoverJob : IJobEntity {
	public float deltaTime;

	public void Execute(
		ref LocalTransform localTransform,
		in UnitMover unitMover,
		ref PhysicsVelocity physicsVelocity
	) {
		var moveDirection = unitMover.TargetPosition - localTransform.Position;
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
	}
}