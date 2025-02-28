using ScriptableObjectArchitecture;
using UnityEngine;

namespace Survivors.Scripts.GameLoop {
	public class GameLoopView : MonoBehaviour {
		public GameEvent gameLoopInitializedEvent;
		public GameEvent gameLoopPostInitializedEvent;
		public GameEvent gameLoopStartedEvent;
		public GameEvent gameLoopPostStartedEvent;
		public GameEvent gameLoopFixedTickEvent;
		public GameEvent gameLoopPostFixedTickEvent;
		public GameEvent gameLoopTickEvent;
		public GameEvent gameLoopPostTickEvent;
		public GameEvent gameLoopLateTickEvent;
		public GameEvent gameLoopPostLateTickEvent;
		public GameEvent gameLoopDisposedEvent;
	}
}