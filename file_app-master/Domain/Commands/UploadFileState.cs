using System.IO;
using NFS;

namespace Domain.Commands
{
    public class UploadFileState : ICommandState
    {
        public UploadFileState(
            NPath target,
            NPath fileName,
            Stream stream)
        {
            Target = target;
            FileName = fileName;
            Stream = stream;
        }

        public NPath Target { get; }
        public NPath FileName { get; }
        public Stream Stream { get; }
    }
}