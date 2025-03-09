using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class HealthAuthoring : MonoBehaviour {
		public float value;
		
		public class Baker : Baker<HealthAuthoring> {
			public override void Bake(HealthAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new Health {
					Value = authoring.value
				});
			}
		}
	}
	
	public struct Health : IComponentData {
		public float Value;
	}
}