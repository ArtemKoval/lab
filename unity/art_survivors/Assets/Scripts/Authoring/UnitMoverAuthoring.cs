using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;

namespace Authoring {
	public class UnitMoverAuthoring : MonoBehaviour {
		public float moveSpeed;
	
		public class Baker : Baker<UnitMoverAuthoring> {
			public override void Bake(UnitMoverAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new UnitMover {
					MoveSpeed = authoring.moveSpeed
				});
			}
		}
	}

	public struct UnitMover : IComponentData {
		public float MoveSpeed;
		public float3 TargetPosition;
	}
}