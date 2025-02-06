using NFS;

namespace Domain.Commands
{
    public class DownloadFileState: ICommandState
    {
        public DownloadFileState(NPath target)
        {
            Target = target;
        }

        public NPath Target { get; }
    }
}