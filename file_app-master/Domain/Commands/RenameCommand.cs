using System;
using System.Threading.Tasks;
using NFS;

namespace Domain.Commands
{
    public class RenameCommand
        : IRenameCommand<RenameResult, object, RenameState>
    {
        private readonly IFileSystem _fileSystem;

        public RenameCommand(IFileSystem fileSystem)
        {
            _fileSystem = fileSystem;
        }

        public RenameCommand(RenameResult result)
        {
            Result = result;
        }

        public async Task<RenameResult> ExecuteAsync(RenameState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public RenameResult Execute(RenameState state)
        {
            try
            {
                // state.target is expected to be relative
                // per UI lib specification
                var destination = _fileSystem.PathCombine(
                    new NPath(System.IO.Path.GetDirectoryName(state.Source.Raw)),
                    state.Target).Raw;

                if (_fileSystem.DirectoryExists(state.Source))
                {
                    _fileSystem.MoveDirectory(state.Source, new NPath(destination));
                }
                else if (_fileSystem.FileExists(state.Source))
                {
                    _fileSystem.MoveFile(state.Source, new NPath(destination));
                }

                Result = new RenameResult(true, new
                {
                    id = destination,
                    value = state.Target.Raw
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new RenameResult(false, null);
            }

            return Result;
        }

        public object GetResult()
        {
            return Result.Result;
        }

        public RenameResult Result { get; private set; }
    }
}