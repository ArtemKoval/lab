using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class EntitiesReferencesAuthoring : MonoBehaviour {
		public GameObject bulletPrefab;

		public class Baker : Baker<EntitiesReferencesAuthoring> {
			public override void Bake(EntitiesReferencesAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new EntitiesReferences {
					BulletPrefabEntity = GetEntity(authoring.bulletPrefab, TransformUsageFlags.Dynamic),
				});
			}
		}
	}

	public struct EntitiesReferences : IComponentData {
		public Entity BulletPrefabEntity;
	}
}