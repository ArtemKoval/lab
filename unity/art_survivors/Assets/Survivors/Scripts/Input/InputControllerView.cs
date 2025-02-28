using ScriptableObjectArchitecture;
using Survivors.Scripts.GameLoop;
using UnityEngine;

namespace Survivors.Scripts.Input {
	public class InputControllerView : MonoBehaviour {
		public Vector3Variable movementInput;
		public GameEvent gameLoopTickEvent;
	}
}