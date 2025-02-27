using CHARK.ScriptableEvents.Events;
using UnityEngine;

namespace Survivors.Scripts.GameLoop {
	public class GameLoopView : MonoBehaviour {
		public SimpleScriptableEvent gameLoopInitializedEvent;
		public SimpleScriptableEvent gameLoopPostInitializedEvent;
		public SimpleScriptableEvent gameLoopStartedEvent;
		public SimpleScriptableEvent gameLoopPostStartedEvent;
		public SimpleScriptableEvent gameLoopFixedTickEvent;
		public SimpleScriptableEvent gameLoopPostFixedTickEvent;
		public SimpleScriptableEvent gameLoopTickEvent;
		public SimpleScriptableEvent gameLoopPostTickEvent;
		public SimpleScriptableEvent gameLoopLateTickEvent;
		public SimpleScriptableEvent gameLoopPostLateTickEvent;
		public SimpleScriptableEvent gameLoopDisposedEvent;
	}
}