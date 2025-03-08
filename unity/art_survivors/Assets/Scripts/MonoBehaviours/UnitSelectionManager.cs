using System;
using Authoring;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Physics;
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
			var movePositionArray = GenerateMovePositionArray(mouseWorldPosition, unitMoverArray.Length);	
			for (var index = 0; index < unitMoverArray.Length; index++) {
				var unitMover = unitMoverArray[index];
				unitMover.TargetPosition = movePositionArray[index];
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
			var selectedArray = entityQuery.ToComponentDataArray<Selected>(Allocator.Temp);
			for (var index = 0; index < entityArray.Length; index++) {
				entityManager.SetComponentEnabled<Selected>(entityArray[index], false);
				var selected = selectedArray[index];
				selected.onDeselected = true;
				entityManager.SetComponentData(entityArray[index], selected);
			}

			var selectionAreaRect = GetSelectionAreaRect();
			var selectionAreaSize = selectionAreaRect.width + selectionAreaRect.height;
			var multipleSelectionSizeMin = 40f;
			var isMultipleSelection = selectionAreaSize > multipleSelectionSizeMin;

			if (isMultipleSelection) {
				entityQuery = new EntityQueryBuilder(Allocator.Temp)
					.WithAll<LocalTransform, Unit>()
					.WithPresent<Selected>()
					.Build(entityManager);


				entityArray = entityQuery.ToEntityArray(Allocator.Temp);
				var localTransformArray = entityQuery.ToComponentDataArray<LocalTransform>(Allocator.Temp);
				for (var index = 0; index < localTransformArray.Length; index++) {
					var unitScreenPosition =
						Camera.main.WorldToScreenPoint(localTransformArray[index].Position);
					if (selectionAreaRect.Contains(unitScreenPosition)) {
						entityManager.SetComponentEnabled<Selected>(entityArray[index], true);
						var selected = entityManager.GetComponentData<Selected>(entityArray[index]);
						selected.onSelected = true;
						entityManager.SetComponentData(entityArray[index], selected);
					}
				}
			}
			else {
				entityQuery = entityManager.CreateEntityQuery(typeof(PhysicsWorldSingleton));
				var physicsWorldSingleton = entityQuery.GetSingleton<PhysicsWorldSingleton>();
				var collisionWorld = physicsWorldSingleton.CollisionWorld;
				var cameraRay = Camera.main.ScreenPointToRay(Input.mousePosition);
				int unitsLayer = 6;
				var raycastInput = new RaycastInput {
					Start = cameraRay.GetPoint(0f),
					End = cameraRay.GetPoint(9999f),
					Filter = new CollisionFilter {
						BelongsTo = ~0u,
						CollidesWith = 1u << unitsLayer,
						GroupIndex = 0
					}
				};
				if (collisionWorld.CastRay(raycastInput, out var hit)) {
					if (entityManager.HasComponent<Unit>(hit.Entity)) {
						entityManager.SetComponentEnabled<Selected>(hit.Entity, true);
						var selected = entityManager.GetComponentData<Selected>(hit.Entity);
						selected.onSelected = true;
						entityManager.SetComponentData(hit.Entity, selected);
					}
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

		private NativeArray<float3> GenerateMovePositionArray(float3 targetPosition, int positioncount) {
			var positionArray = new NativeArray<float3>(positioncount, Allocator.Temp);
			if (positioncount == 0)	return positionArray;
			positionArray[0] = targetPosition;
			if (positioncount == 1) return positionArray;
			float ringSize = 2.2f;
			int ring = 0;
			int positionIndex = 1;
			while (positionIndex < positioncount) {
				var ringPositionCount = 3 + ring * 2;
				for (var i = 0; i < ringPositionCount; i++) {
					var angle = i * (math.PI2 / ringPositionCount);
					var ringVector = math.rotate(quaternion.RotateY(angle), new float3(ringSize * (ring + 1), 0, 0));
					var ringPosition = targetPosition + ringVector;
					positionArray[positionIndex] = ringPosition;
					positionIndex++;
					if (positionIndex >= positioncount) {
						break;
					}
				}
				ring++;
			}
			return positionArray;
		}
	}
}