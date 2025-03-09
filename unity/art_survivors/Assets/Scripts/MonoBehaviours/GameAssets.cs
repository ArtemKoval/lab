using UnityEngine;

namespace MonoBehaviours {
	public class GameAssets : MonoBehaviour {
		public const int UnitsLayer = 6;
		
		public static GameAssets Instance { get; private set; }

		private void Awake() {
			Instance = this;
		}
	}
}