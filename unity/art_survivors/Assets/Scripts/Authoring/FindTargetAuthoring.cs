using Unity.Entities;
using UnityEngine;

namespace Authoring {
	public class FindTargetAuthoring : MonoBehaviour {
		public float range;
		public Faction faction;
		public float timerMax;

		public class Baker : Baker<FindTargetAuthoring> {
			public override void Bake(FindTargetAuthoring authoring) {
				var entity = GetEntity(TransformUsageFlags.Dynamic);
				AddComponent(entity, new FindTarget {
					Range = authoring.range,
					Faction = authoring.faction,
					TimerMax = authoring.timerMax
				});
			}
		}
	}

	public struct FindTarget : IComponentData {
		public float Range;
		public Faction Faction;
		public float Timer;
		public float TimerMax;
	}
}