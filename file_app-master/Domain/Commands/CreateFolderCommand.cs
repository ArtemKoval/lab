using System;
using System.Threading.Tasks;
using NFS;

namespace Domain.Commands
{
    public class CreateFolderCommand
        : ICreateFolderCommand<CreateFolderResult, object, CreateFolderState>
    {
        private readonly IFileSystem _fileSystem;

        // TODO: add abstract class to capture ctor and executeasync
        public CreateFolderCommand(IFileSystem fileSystem)
        {
            _fileSystem = fileSystem;
        }

        public async Task<CreateFolderResult> ExecuteAsync(CreateFolderState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public CreateFolderResult Execute(CreateFolderState state)
        {
            try
            {
                var path = _fileSystem.PathCombine(state.Target, state.Source);
                _fileSystem.CreateDirectory(path);

                Result = new CreateFolderResult(true, new
                {
                    id = path.Raw,
                    value = state.Source.Raw
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new CreateFolderResult(false, null);
            }

            return Result;
        }

        public object GetResult()
        {
            return Result.Result;
        }

        public CreateFolderResult Result { get; private set; }
    }
}