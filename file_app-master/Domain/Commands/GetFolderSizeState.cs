using NFS;

namespace Domain.Commands
{
    public class GetFolderSizeState : ICommandState
    {
        public GetFolderSizeState(NPath target)
        {
            Target = target;
        }

        public NPath Target { get; }
    }
}