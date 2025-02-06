using NFS;

namespace Domain.Commands
{
    public class RenameState: ICommandState
    {
        public RenameState(NPath target,
            NPath source)
        {
            Target = target;
            Source = source;
        }

        public NPath Target { get; }
        
        public NPath Source { get; }
    }
}