using System;
using Authoring;
using Unity.Collections;
using Unity.Entities;
using Unity.Transforms;
using UnityEngine;

namespace MonoBehaviours {
	public class UnitSelectionManager : MonoBehaviour {
		public static UnitSelectionManager Instance { get; private set; }

		private Vector2 _selectionStartMousePosition;
		public event EventHandler OnSelectionAreaStart;
		public event EventHandler OnSelectionAreaEnd;

		private void Awake() {
			Instance = this;
		}

		private void Update() {
			if (Input.GetMouseButtonDown(0)) {
				_selectionStartMousePosition = Input.mousePosition;
				OnSelectionAreaStart?.Invoke(this, EventArgs.Empty);
			}

			if (Input.GetMouseButtonUp(0)) {
				SelectUnits();
			}

			if (!Input.GetMouseButtonDown(1)) return;
			var mouseWorldPosition = MouseWorldPosition.Instance.GetWorldPosition();
			var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
			var entityQuery = new EntityQueryBuilder(Allocator.Temp)
				.WithAll<UnitMover, Selected>().Build(entityManager);
			var unitMoverArray = entityQuery.ToComponentDataArray<UnitMover>(Allocator.Temp);
			for (var index = 0; index < unitMoverArray.Length; index++) {
				var unitMover = unitMoverArray[index];
				unitMover.TargetPosition = mouseWorldPosition;
				unitMoverArray[index] = unitMover;
			}

			entityQuery.CopyFromComponentDataArray(unitMoverArray);
		}

		private void SelectUnits() {
			var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;

			var entityQuery = new EntityQueryBuilder(Allocator.Temp)
				.WithAll<Selected>()
				.Build(entityManager);
			var entityArray = entityQuery.ToEntityArray(Allocator.Temp);
			for (var index = 0; index < entityArray.Length; index++) {
				entityManager.SetComponentEnabled<Selected>(entityArray[index], false);
			}

			entityQuery = new EntityQueryBuilder(Allocator.Temp)
				.WithAll<LocalTransform, Unit>()
				.WithPresent<Selected>()
				.Build(entityManager);

			var selectionAreaRect = GetSelectionAreaRect();
			entityArray = entityQuery.ToEntityArray(Allocator.Temp);
			var localTransformArray = entityQuery.ToComponentDataArray<LocalTransform>(Allocator.Temp);
			for (var index = 0; index < localTransformArray.Length; index++) {
				var unitScreenPosition =
					Camera.main.WorldToScreenPoint(localTransformArray[index].Position);
				if (selectionAreaRect.Contains(unitScreenPosition)) {
					entityManager.SetComponentEnabled<Selected>(entityArray[index], true);
				}
			}

			OnSelectionAreaEnd?.Invoke(this, EventArgs.Empty);
		}

		public Rect GetSelectionAreaRect() {
			var selectionEndMousePosition = Input.mousePosition;

			var lowerLeftCorner = new Vector2(
				Mathf.Min(_selectionStartMousePosition.x, selectionEndMousePosition.x),
				Mathf.Min(_selectionStartMousePosition.y, selectionEndMousePosition.y)
			);

			var upperRightCorner = new Vector2(
				Mathf.Max(_selectionStartMousePosition.x, selectionEndMousePosition.x),
				Mathf.Max(_selectionStartMousePosition.y, selectionEndMousePosition.y)
			);

			return new Rect(
				lowerLeftCorner.x,
				lowerLeftCorner.y,
				upperRightCorner.x - lowerLeftCorner.x,
				upperRightCorner.y - lowerLeftCorner.y);
		}
	}
}