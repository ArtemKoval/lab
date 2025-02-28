using ScriptableObjectArchitecture;
using UnityEngine;
using UnityEngine.Serialization;

namespace Survivors.Scripts.Spawn {
	[CreateAssetMenu(fileName = "PlayerSpawnController",
		menuName = "_Survivors/Scriptable Objects/PlayerSpawnController")]
	public class PlayerSpawnController : ScriptableObject {
		public GameObjectReference playerPrefab;
		public GameObjectReference playerGameObject;

		public void SpawnPlayer() {
			var player = Instantiate(playerPrefab.Value, new Vector3(0, 0, 0), Quaternion.identity);
			playerGameObject.Value = player;
		}
	}
}