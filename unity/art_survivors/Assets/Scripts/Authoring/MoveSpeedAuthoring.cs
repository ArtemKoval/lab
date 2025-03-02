using UnityEngine;
using Unity.Entities;

public class MoveSpeedAuthoring : MonoBehaviour {
	public float value;
	
	public class Baker : Baker<MoveSpeedAuthoring> {
		public override void Bake(MoveSpeedAuthoring authoring) {
			var entity = GetEntity(TransformUsageFlags.Dynamic);
			AddComponent(entity, new MoveSpeed {
				Value = authoring.value
			});
		}
	}
}

public struct MoveSpeed : IComponentData {
	public float Value;
}