using Authoring;
using Unity.Collections;
using Unity.Entities;
using UnityEngine;

namespace MonoBehaviours {
	public class UnitSelectionManager : MonoBehaviour {
		private void Update() {
			if (!Input.GetMouseButtonDown(1)) return;
			var mouseWorldPosition = MouseWorldPosition.Instance.GetWorldPosition();
			var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
			var entityQuery = new EntityQueryBuilder(Allocator.Temp).WithAll<UnitMover>().Build(entityManager);
			var unitMoverArray = entityQuery.ToComponentDataArray<UnitMover>(Allocator.Temp);
			for (var index = 0; index < unitMoverArray.Length; index++) {
				var unitMover = unitMoverArray[index];
				unitMover.TargetPosition = mouseWorldPosition;
				unitMoverArray[index] = unitMover;
			}

			entityQuery.CopyFromComponentDataArray(unitMoverArray);
		}
	}
}