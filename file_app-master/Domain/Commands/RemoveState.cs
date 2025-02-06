using NFS;

namespace Domain.Commands
{
    public class RemoveState : ICommandState
    {
        public RemoveState(NPath target)
        {
            Target = target;
        }

        public NPath Target { get; }
    }
}