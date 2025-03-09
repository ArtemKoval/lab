using Authoring;
using MonoBehaviours;
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Physics;
using Unity.Transforms;

namespace Systems {
	partial struct FindTargetSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var physicsWorldSingleton = SystemAPI.GetSingleton<PhysicsWorldSingleton>();
			var collisionWorld = physicsWorldSingleton.CollisionWorld;
			var distanceHitList = new NativeList<DistanceHit>(Allocator.Temp);
			foreach (var (localTransform, findTarget, target)
			         in SystemAPI.Query<RefRO<LocalTransform>,
				         RefRW<FindTarget>,
				         RefRW<Target>>()) {
				findTarget.ValueRW.Timer -= SystemAPI.Time.DeltaTime;
				if (findTarget.ValueRO.Timer > 0f) {
					continue;
				}

				findTarget.ValueRW.Timer = findTarget.ValueRO.TimerMax;

				distanceHitList.Clear();
				var collisionFilter = new CollisionFilter {
					BelongsTo = ~0u,
					CollidesWith = 1u << GameAssets.UnitsLayer,
					GroupIndex = 0
				};
				if (collisionWorld.OverlapSphere(localTransform.ValueRO.Position,
					    findTarget.ValueRO.Range,
					    ref distanceHitList, collisionFilter)) {
					foreach (var distanceHit in distanceHitList) {
						var targetUnit = SystemAPI.GetComponent<Unit>(distanceHit.Entity);
						if (targetUnit.Faction == findTarget.ValueRO.Faction) {
							target.ValueRW.TargetEntity = distanceHit.Entity;
							break;
						}
					}
				}
				// else {
				// 	target.ValueRW.TargetEntity = Entity.Null;
				// }
			}
		}
	}
}