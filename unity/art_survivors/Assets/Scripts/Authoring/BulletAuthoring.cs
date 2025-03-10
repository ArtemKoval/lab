using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class BulletAuthoring : MonoBehaviour {
		public float speed;
		public float damageAmount;
		public class Baker : Baker<BulletAuthoring> {
			public override void Bake(BulletAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new Bullet {
					Speed = authoring.speed,
					DamageAmount = authoring.damageAmount
				});
			}
		}
	}

	public struct Bullet : IComponentData {
		public float Speed;
		public float DamageAmount;
	}
}