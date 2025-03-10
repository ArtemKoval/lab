using Authoring;
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

namespace Systems {
	partial struct BulletMoverSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var entityCommandBuffer = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>()
				.CreateCommandBuffer(state.WorldUnmanaged);


			foreach (var (localTransform, bullet, target, entity)
			         in SystemAPI.Query<RefRW<LocalTransform>, RefRO<Bullet>, RefRO<Target>>().WithEntityAccess()) {
				if (target.ValueRO.TargetEntity == Entity.Null) {
					entityCommandBuffer.DestroyEntity(entity);
					continue;
				}
				
				var targetLocalTransform =
					SystemAPI.GetComponentRO<LocalTransform>(target.ValueRO.TargetEntity);
				var distanceBeforeSq = math.distancesq(targetLocalTransform.ValueRO.Position, localTransform.ValueRO.Position);
				var direction = targetLocalTransform.ValueRO.Position
				                - localTransform.ValueRO.Position;
				direction = math.normalize(direction);
				localTransform.ValueRW.Position += direction * bullet.ValueRO.Speed * SystemAPI.Time.DeltaTime;
				var distanceAfterSq = math.distancesq(targetLocalTransform.ValueRO.Position, localTransform.ValueRO.Position);
				if (distanceAfterSq > distanceBeforeSq) {
					localTransform.ValueRW.Position = targetLocalTransform.ValueRO.Position;
				}

				const float destroyDistanceSq = .2f;
				if (!(math.distancesq(targetLocalTransform.ValueRO.Position, localTransform.ValueRO.Position) <
				      destroyDistanceSq)) continue;
				var targetHealth = SystemAPI.GetComponentRW<Health>(target.ValueRO.TargetEntity);
				targetHealth.ValueRW.Value -= bullet.ValueRO.DamageAmount;
				entityCommandBuffer.DestroyEntity(entity);
			}
		}
	}
}