using System;
using System.IO;
using System.Threading.Tasks;
using Domain.FileSystem;
using NFS;

namespace Domain.Commands
{
    public class UploadFileCommand
        : IUploadFileCommand<UploadFileResult, object, UploadFileState>
    {
        private readonly IFileSystem _fileSystem;

        public UploadFileCommand(IFileSystem fileSystem)
        {
            _fileSystem = fileSystem;
        }

        public async Task<UploadFileResult> ExecuteAsync(UploadFileState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public UploadFileResult Execute(UploadFileState state)
        {
            try
            {
                var path = _fileSystem.PathCombine(
                    state.Target,
                    state.FileName);

                using (var stream = _fileSystem.OpenFile(
                    path,
                    FileMode.Create,
                    FileAccess.Write,
                    FileShare.Write))
                {
                    state.Stream.CopyTo(stream);
                }

                Result = new UploadFileResult(true, new
                {
                    folder = Path.GetFileName( Path.GetDirectoryName(path.Raw)),
                    value = state.FileName.Raw,
                    id = path.Raw,
                    type = NodeType.File,
                    status = "server"
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new UploadFileResult(false, null);
            }

            return Result;
        }

        public object GetResult()
        {
            return Result.Result;
        }

        public UploadFileResult Result { get; private set; }
    }
}