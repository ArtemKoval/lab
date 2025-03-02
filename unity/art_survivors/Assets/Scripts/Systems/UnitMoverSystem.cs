using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

namespace Systems {
	public partial struct UnitMoverSystem : ISystem {
		[BurstCompile]
		public void OnUpdate(ref SystemState state) {
			foreach (var (localTransform, moveSpeed)
			         in SystemAPI.Query<
				         RefRW<LocalTransform>,
				         RefRO<MoveSpeed>>()) {
				localTransform.ValueRW.Position =
					localTransform.ValueRO.Position +
					new float3(1, 0, 0) * moveSpeed.ValueRO.Value * SystemAPI.Time.DeltaTime;
			}
		}
	}
}