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
			foreach (var (localTransform,
				         unitMover,
				         physicsVelocity)
			         in SystemAPI.Query<
					         RefRW<LocalTransform>,
					         RefRO<UnitMover>,
					         RefRW<PhysicsVelocity>>
				         ()) {
				var moveDirection = unitMover.ValueRO.TargetPosition - localTransform.ValueRO.Position;
				moveDirection = math.normalizesafe(moveDirection);

				// for 2d use sprite flip instead of rotation todo
				// localTransform.ValueRW.Rotation = quaternion.LookRotation(moveDirection, math.up());

				physicsVelocity.ValueRW.Linear = moveDirection * unitMover.ValueRO.MoveSpeed;
				physicsVelocity.ValueRW.Angular = float3.zero; // freeze rotation on collisions
			}
		}
	}
}