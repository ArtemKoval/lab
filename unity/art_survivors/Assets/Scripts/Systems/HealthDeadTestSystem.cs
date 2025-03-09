using Authoring;
using Unity.Burst;
using Unity.Entities;

namespace Systems {
	[UpdateInGroup(typeof(LateSimulationSystemGroup))]
	partial struct HealthDeadTestSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			var entityCommandBuffer = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>()
				.CreateCommandBuffer(state.WorldUnmanaged);
			foreach (var (health, entity)
			         in SystemAPI.Query<RefRO<Health>>()
				         .WithEntityAccess()) {
				if (health.ValueRO.Value <= 0f) {
					entityCommandBuffer.DestroyEntity(entity);
				}
			}
		}
	}
}