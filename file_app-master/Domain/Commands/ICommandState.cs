using NFS;

namespace Domain.Commands
{
    public interface ICommandState
    {
        NPath Target { get; }
    }
}