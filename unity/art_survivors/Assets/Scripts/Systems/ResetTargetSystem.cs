using Authoring;
using Unity.Burst;
using Unity.Entities;

namespace Systems {
	[UpdateInGroup(typeof(LateSimulationSystemGroup))]
	partial struct ResetTargetSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			foreach (var target in SystemAPI.Query<RefRW<Target>>()) {
				if (!SystemAPI.Exists(target.ValueRO.TargetEntity)) target.ValueRW.TargetEntity = Entity.Null;
			}
		}
	}
}