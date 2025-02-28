using System;
using JetBrains.Annotations;
using ScriptableObjectArchitecture;
using Survivors.Scripts.GameLoop;
using VContainer.Unity;

namespace Survivors.Scripts.DependencyInjection {
	[UsedImplicitly]
	public class GameLoopEmitter : IInitializable, IPostInitializable, IStartable, IPostStartable,
		IFixedTickable, IPostFixedTickable, ITickable, IPostTickable, ILateTickable, IPostLateTickable, IDisposable {
		private GameEvent _gameLoopInitializedEvent;
		private GameEvent _gameLoopPostInitializedEvent;
		private GameEvent _gameLoopStartedEvent;
		private GameEvent _gameLoopPostStartedEvent;
		private GameEvent _gameLoopFixedTickEvent;
		private GameEvent _gameLoopPostFixedTickEvent;
		private GameEvent _gameLoopTickEvent;
		private GameEvent _gameLoopPostTickEvent;
		private GameEvent _gameLoopLateTickEvent;
		private GameEvent _gameLoopPostLateTickEvent;
		private GameEvent _gameLoopDisposedEvent;


		private readonly GameLoopView _gameLoopView;

		public GameLoopEmitter(
			GameLoopView gameLoopView
		) {
			_gameLoopView = gameLoopView;

			InitializeEvents();
		}

		private void InitializeEvents() {
			_gameLoopInitializedEvent = _gameLoopView.gameLoopInitializedEvent;
			_gameLoopPostInitializedEvent = _gameLoopView.gameLoopPostInitializedEvent;
			_gameLoopStartedEvent = _gameLoopView.gameLoopStartedEvent;
			_gameLoopPostStartedEvent = _gameLoopView.gameLoopPostStartedEvent;
			_gameLoopFixedTickEvent = _gameLoopView.gameLoopFixedTickEvent;
			_gameLoopPostFixedTickEvent = _gameLoopView.gameLoopPostFixedTickEvent;
			_gameLoopTickEvent = _gameLoopView.gameLoopTickEvent;
			_gameLoopPostTickEvent = _gameLoopView.gameLoopPostTickEvent;
			_gameLoopLateTickEvent = _gameLoopView.gameLoopLateTickEvent;
			_gameLoopPostLateTickEvent = _gameLoopView.gameLoopPostLateTickEvent;
			_gameLoopDisposedEvent = _gameLoopView.gameLoopDisposedEvent;
		}


		public void Initialize() {
			_gameLoopInitializedEvent.Raise();
		}

		public void PostInitialize() {
			_gameLoopPostInitializedEvent.Raise();
		}

		public void Start() {
			_gameLoopStartedEvent.Raise();
		}

		public void PostStart() {
			_gameLoopPostStartedEvent.Raise();
		}

		public void FixedTick() {
			_gameLoopFixedTickEvent.Raise();
		}

		public void PostFixedTick() {
			_gameLoopPostFixedTickEvent.Raise();
		}

		public void Tick() {
			_gameLoopTickEvent.Raise();
		}

		public void PostTick() {
			_gameLoopPostTickEvent.Raise();
		}

		public void LateTick() {
			_gameLoopLateTickEvent.Raise();
		}

		public void PostLateTick() {
			_gameLoopPostLateTickEvent.Raise();
		}

		public void Dispose() {
			_gameLoopDisposedEvent.Raise();
		}
	}
}