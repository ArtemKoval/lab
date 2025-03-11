using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class ShootAttackAuthoring : MonoBehaviour {
		public float timerMax = 1f;
		public float damageAmount = 1f;
		public float attackDistance = 10f;
		
		public class Baker : Baker<ShootAttackAuthoring> {
			public override void Bake(ShootAttackAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new ShootAttack {
					TimerMax = authoring.timerMax,
					DamageAmount = authoring.damageAmount,
					AttackDistance = authoring.attackDistance
					
					
				});
			}
		}
	}

	public struct ShootAttack : IComponentData {
		public float Timer;
		public float TimerMax;
		public float DamageAmount;
		public float AttackDistance;
	}
}