using Survivors.Scripts.GameLoop;
using UnityEngine;
using VContainer;
using VContainer.Unity;

namespace Survivors.Scripts.DependencyInjection {
	public class GameLifetimeScope : LifetimeScope {
		[SerializeField] private GameLoopView gameLoopView;

		protected override void Configure(IContainerBuilder builder) {
			builder.RegisterEntryPoint<GameLoopEmitter>();
			builder.RegisterComponent(gameLoopView);
		}
	}
}