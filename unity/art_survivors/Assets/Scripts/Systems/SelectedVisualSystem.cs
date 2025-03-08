using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

namespace Systems {
	[UpdateInGroup(typeof(LateSimulationSystemGroup))]
	[UpdateBefore(typeof(ResetEventsSystem))]
	public partial struct SelectedVisualSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			foreach (var selected in SystemAPI.Query<RefRO<Selected>>().WithPresent<Selected>()) {
				if (selected.ValueRO.onSelected) {
					var visualLocalTransform = SystemAPI.GetComponentRW<LocalTransform>(selected.ValueRO.VisualEntity);
					visualLocalTransform.ValueRW.Scale = selected.ValueRO.ShowScale;
				}

				if (selected.ValueRO.onDeselected) {
					var visualLocalTransform = SystemAPI.GetComponentRW<LocalTransform>(selected.ValueRO.VisualEntity);
					visualLocalTransform.ValueRW.Scale = 0f;
				}
			}
		}
	}
}