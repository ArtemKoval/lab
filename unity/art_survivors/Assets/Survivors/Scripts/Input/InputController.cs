using JetBrains.Annotations;
using ScriptableObjectArchitecture;
using UnityEngine;

namespace Survivors.Scripts.Input {
	[UsedImplicitly]
	[CreateAssetMenu(fileName = "InputController", menuName = "_Survivors/Scriptable Objects/InputController")]
	public class InputController : ScriptableObject {
		public Vector3Reference movementInput;

		public void OnGameLoopTick() {
			var input = new Vector3 {
				x = UnityEngine.Input.GetAxisRaw("Horizontal"),
				y = UnityEngine.Input.GetAxis("Vertical")
			};

			movementInput.Value = input;
		}
	}
}