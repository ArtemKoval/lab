using NFS;

namespace Domain.Commands
{
    public class CopyState: ICommandState
    {
        public CopyState(NPath target,
            NPath source)
        {
            Target = target;
            Source = source;
        }

        public NPath Target { get; }
        public NPath Source { get; }
    }
}