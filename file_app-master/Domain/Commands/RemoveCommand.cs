using System;
using System.Threading.Tasks;
using NFS;

namespace Domain.Commands
{
    public class RemoveCommand
        : IRemoveCommand<RemoveResult, bool, RemoveState>
    {
        private readonly IFileSystem _fileSystem;

        public RemoveCommand(IFileSystem fileSystem)
        {
            _fileSystem = fileSystem;
        }
        
        public RemoveResult Result { get; private set; }

        public async Task<RemoveResult> ExecuteAsync(RemoveState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public RemoveResult Execute(RemoveState state)
        {
            try
            {
                var targets = state.Target.Raw.Split(",");

                foreach (var target in targets)
                {
                    // TODO: implicit/explicit conversion operators to/from string for NPath
                    if (_fileSystem.DirectoryExists(new NPath(target)))
                    {
                        _fileSystem.DeleteDirectory(new NPath(target), true);
                    }
                    else if (_fileSystem.FileExists(new NPath(target)))
                    {
                        _fileSystem.DeleteFile(new NPath(target));
                    }
                }

                Result = new RemoveResult(true, new[]
                {
                    "ok"
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new RemoveResult(false, null);
            }

            return Result;
        }

        public bool GetResult()
        {
            throw new NotImplementedException();
        }
    }
}