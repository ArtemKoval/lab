using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class SelectedAuthoring : MonoBehaviour {
		public GameObject visualGameObject;
		public float showScale;

		public class Baker : Baker<SelectedAuthoring> {
			public override void Bake(SelectedAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new Selected {
					VisualEntity = GetEntity(authoring.visualGameObject, TransformUsageFlags.Dynamic),
					ShowScale = authoring.showScale
				});
				SetComponentEnabled<Selected>(entity, false);
			}
		}
	}
}

public struct Selected : IComponentData, IEnableableComponent {
	public Entity VisualEntity;
	public float ShowScale;
}