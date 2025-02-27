using VContainer;
using VContainer.Unity;

namespace Survivors.Scripts {
	public class GameLifetimeScope : LifetimeScope {
		protected override void Configure(IContainerBuilder builder) {
			builder.Register<HelloWorldService>(Lifetime.Singleton);
			builder.RegisterEntryPoint<GamePresenter>();
		}
	}
}