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

		public bool useControllerMove = true;

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

			var controllerInput = new Vector3(
					Input.GetAxisRaw("Horizontal"),
					0,
					Input.GetAxisRaw("Vertical"))
				.normalized;

			if (Input.GetMouseButtonUp(0)) {
				SelectUnits();
				return;
			}

			if (controllerInput.x == 0
			    & controllerInput.y == 0
			    & Input.GetMouseButtonDown(1)) {
				MouseMove();
				return;
			}

			// ControllerMove(controllerInput);
			
			// if (controllerInput.x != 0 || controllerInput.y != 0) {
			// 	ControllerMove(controllerInput);
			// 	Debug.Log("Moving with controller");
			// 	return;
			// }
		}

		private void ControllerMove(Vector3 input) {
			MoveUnit(input.normalized, true);
		}

		private void MouseMove() {
			var targetWorldPosition = MouseWorldPosition.Instance.GetWorldPosition();
			MoveUnit(targetWorldPosition);
		}

		private void MoveUnit(float3 targetWorldPosition, bool withController = false) {
			var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
			var entityQuery = new EntityQueryBuilder(Allocator.Temp)
				.WithAll<UnitMover, Selected>().Build(entityManager);
			var unitMoverArray = entityQuery.ToComponentDataArray<UnitMover>(Allocator.Temp);
			var movePositionArray = GenerateMovePositionArray(targetWorldPosition, unitMoverArray.Length);
			for (var index = 0; index < unitMoverArray.Length; index++) {
				var unitMover = unitMoverArray[index];
				unitMover.TargetPosition = movePositionArray[index];
				unitMover.IsController = withController;
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
			const float multipleSelectionSizeMin = 40f;
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
				const float distance = 9999f;
				var raycastInput = new RaycastInput {
					Start = cameraRay.GetPoint(0f),
					End = cameraRay.GetPoint(distance),
					Filter = new CollisionFilter {
						BelongsTo = ~0u,
						CollidesWith = 1u << GameAssets.UnitsLayer,
						GroupIndex = 0
					}
				};
				if (collisionWorld.CastRay(raycastInput, out var hit)) {
					if (entityManager.HasComponent<Unit>(hit.Entity) && entityManager.HasComponent<Selected>(hit.Entity)) {
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

		private NativeArray<float3> GenerateMovePositionArray(float3 targetPosition, int positionCount) {
			var positionArray = new NativeArray<float3>(positionCount, Allocator.Temp);
			if (positionCount == 0) return positionArray;
			positionArray[0] = targetPosition;
			if (positionCount == 1) return positionArray;
			var ringSize = 2.2f;
			var ring = 0;
			var positionIndex = 1;
			while (positionIndex < positionCount) {
				var ringPositionCount = 3 + ring * 2;
				for (var i = 0; i < ringPositionCount; i++) {
					var angle = i * (math.PI2 / ringPositionCount);
					var ringVector = math.rotate(quaternion.RotateY(angle), new float3(ringSize * (ring + 1), 0, 0));
					var ringPosition = targetPosition + ringVector;
					positionArray[positionIndex] = ringPosition;
					positionIndex++;
					if (positionIndex >= positionCount) {
						break;
					}
				}

				ring++;
			}

			return positionArray;
		}
	}
}