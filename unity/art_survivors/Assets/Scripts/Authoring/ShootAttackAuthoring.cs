using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class ShootAttackAuthoring : MonoBehaviour {
		public float timerMax = 1f;
		public float damageAmount = 1f;
		
		public class Baker : Baker<ShootAttackAuthoring> {
			public override void Bake(ShootAttackAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new ShootAttack {
					TimerMax = authoring.timerMax,
					DamageAmount = authoring.damageAmount
				});
			}
		}
	}

	public struct ShootAttack : IComponentData {
		public float Timer;
		public float TimerMax;
		public float DamageAmount;
	}
}