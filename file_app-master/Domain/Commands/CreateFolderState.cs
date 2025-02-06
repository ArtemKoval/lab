using NFS;

namespace Domain.Commands
{
    public class CreateFolderState : ICommandState
    {
        public CreateFolderState(NPath target,
            NPath source)
        {
            Target = target;
            Source = source;
        }

        public NPath Target { get; }
        public NPath Source { get; }
    }
}