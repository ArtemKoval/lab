using Unity.Burst;
using Unity.Entities;

namespace Systems {
	[UpdateInGroup(typeof(LateSimulationSystemGroup))]
	partial struct ResetEventsSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			foreach (var selected in SystemAPI.Query<RefRW<Selected>>().WithPresent<Selected>()) {
				selected.ValueRW.onSelected = false;
				selected.ValueRW.onDeselected = false;
			}
		}
	}
}