using ScriptableObjectArchitecture;
using UnityEngine;

namespace Survivors.Scripts.Movement {
	[CreateAssetMenu(fileName = "PlayerMovementController",
		menuName = "_Survivors/Scriptable Objects/PlayerMovementController")]
	public class PlayerMovementController : ScriptableObject {
		public Vector3Reference movementInput;
		public FloatReference movementSpeed;
		public GameObjectReference playerGameObject;

		public void OnMovementInput() {
			var input = movementInput.Value;
			input.Normalize();
			playerGameObject.Value.transform.position += input * movementSpeed.Value * Time.deltaTime;
		}
	}
}