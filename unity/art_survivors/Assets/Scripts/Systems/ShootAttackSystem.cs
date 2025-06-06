using Authoring;
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

namespace Systems {
	partial struct ShootAttackSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var entitiesReferences = SystemAPI.GetSingleton<EntitiesReferences>();
			foreach (var (localTransform,
				         shootAttack,
				         target,
				         unitMover)
			         in SystemAPI.Query<RefRO<LocalTransform>, RefRW<ShootAttack>, RefRO<Target>, RefRW<UnitMover>>()) {
				if (target.ValueRO.TargetEntity == Entity.Null) continue;
				var targetLocalTransform = SystemAPI.GetComponent<LocalTransform>(target.ValueRO.TargetEntity);

				if (math.distance(localTransform.ValueRO.Position, targetLocalTransform.Position) >
				    shootAttack.ValueRO.AttackDistance) {
					unitMover.ValueRW.TargetPosition = targetLocalTransform.Position;
					continue;
				}
				shootAttack.ValueRW.Timer -= SystemAPI.Time.DeltaTime;
				if (shootAttack.ValueRO.Timer > 0f) continue;
				shootAttack.ValueRW.Timer = shootAttack.ValueRO.TimerMax;



				unitMover.ValueRW.TargetPosition = targetLocalTransform.Position;
				var bulletEntity = state.EntityManager.Instantiate(entitiesReferences.BulletPrefabEntity);
				SystemAPI.SetComponent(bulletEntity,
					LocalTransform.FromPosition(localTransform.ValueRO.Position));
				var bullet = SystemAPI.GetComponentRW<Bullet>(bulletEntity);
				bullet.ValueRW.DamageAmount = shootAttack.ValueRO.DamageAmount;
				var bulletTarget = SystemAPI.GetComponentRW<Target>(bulletEntity);
				bulletTarget.ValueRW.TargetEntity = target.ValueRO.TargetEntity;
			}
		}
	}
}