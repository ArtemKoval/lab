using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

namespace Systems {
	public partial struct SelectedVisualSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			foreach (var selected in SystemAPI.Query<RefRO<Selected>>().WithDisabled<Selected>()) {
				var visualLocalTransform = SystemAPI.GetComponentRW<LocalTransform>(selected.ValueRO.VisualEntity);
				visualLocalTransform.ValueRW.Scale = 0f;
			}
			
			foreach (var selected in SystemAPI.Query<RefRO<Selected>>()) {
				var visualLocalTransform = SystemAPI.GetComponentRW<LocalTransform>(selected.ValueRO.VisualEntity);
				visualLocalTransform.ValueRW.Scale = selected.ValueRO.ShowScale;
			}
		}
	}
}