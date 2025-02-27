using JetBrains.Annotations;

namespace Survivors.Scripts.DependencyInjection {
	[UsedImplicitly]
	public class HelloWorldService {
		public void Hello() {
			UnityEngine.Debug.Log("Hello world");
		}
	}
}