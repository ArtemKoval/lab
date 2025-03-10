using Authoring;
using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

namespace Systems {
	partial struct ShootAttackSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var entitiesReferences = SystemAPI.GetSingleton<EntitiesReferences>();
			foreach (var (localTransform,
				         shootAttack,
				         target)
			         in SystemAPI.Query<RefRO<LocalTransform>, RefRW<ShootAttack>, RefRO<Target>>()) {
				if (target.ValueRO.TargetEntity == Entity.Null) continue;
				shootAttack.ValueRW.Timer -= SystemAPI.Time.DeltaTime;
				if (shootAttack.ValueRO.Timer > 0f) continue;
				shootAttack.ValueRW.Timer += shootAttack.ValueRO.TimerMax;

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