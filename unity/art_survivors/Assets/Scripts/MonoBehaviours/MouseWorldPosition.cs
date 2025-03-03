using UnityEngine;

public class MouseWorldPosition : MonoBehaviour {
	public static MouseWorldPosition Instance { get; private set; }

	private void Awake() {
		Instance = this;
	}

	public Vector3 GetWorldPosition() {
		if (Camera.main == null) return Vector3.zero;
		var ray = Camera.main.ScreenPointToRay(Input.mousePosition);
		return Physics.Raycast(ray, out var hit) ? hit.point : Vector3.zero;
	}
}