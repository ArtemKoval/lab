using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using NFS;

namespace Domain.Commands
{
    public class CopyCommand
        : ICopyCommand<CopyResult, object, CopyState>
    {
        private readonly IFileSystem _fileSystem;

        public CopyCommand(IFileSystem fileSystem)
        {
            _fileSystem = fileSystem;
        }

        public async Task<CopyResult> ExecuteAsync(CopyState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public CopyResult Execute(CopyState state)
        {
            try
            {
                var sources = state.Source.Raw.Split(",");
                var result = new List<object>();

                foreach (var source in sources)
                {
                    if (_fileSystem.DirectoryExists(new NPath(source)))
                    {
                        var directoryResult = CopyDirectory(state, source);
                        result.Add(directoryResult);
                    }
                    else if (_fileSystem.FileExists(new NPath(source)))
                    {
                        var fileResult = CopyFile(state, source);
                        result.Add(fileResult);
                    }
                }

                Result = new CopyResult(true, result);
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new CopyResult(false, null);
            }

            return Result;
        }

        private static void CopyAll(DirectoryInfo source, DirectoryInfo target)
        {
            System.IO.Directory.CreateDirectory(target.FullName);

            foreach (var fileInfo in source.GetFiles())
            {
                fileInfo
                    .CopyTo(Path.Combine(target.FullName, fileInfo.Name), true);
            }

            foreach (var directoryInfo in source.GetDirectories())
            {
                var nextTargetSubDir =
                    target.CreateSubdirectory(directoryInfo.Name);
                CopyAll(directoryInfo, nextTargetSubDir);
            }
        }

        
        private object CopyDirectory(ICommandState state, string source)
        {
            var folder = source;
            var folderName = new DirectoryInfo(source).Name;
            var copyFolderName = $"Copy of {folderName}";

            var destination = _fileSystem.PathCombine(
                _fileSystem.PathCombine(new NPath(folder), new NPath(state.Target.Raw)),
                new NPath(copyFolderName));

            while (_fileSystem.DirectoryExists(destination))
            {
                folderName = new DirectoryInfo(destination.Raw).Name;
                copyFolderName = $"Copy of {folderName}";
                destination = _fileSystem.PathCombine(
                    _fileSystem.PathCombine(new NPath(folder), new NPath(state.Target.Raw)),
                    new NPath(copyFolderName));
            }
            
            CopyAll(new DirectoryInfo(source), new DirectoryInfo(destination.Raw));
            
            var folderResult = new
            {
                id = destination.Raw,
                value = copyFolderName
            };

            return folderResult;
        }
        
        private object CopyFile(ICommandState state, string source)
        {
            // TODO: Run some tests on methods equivalency
            // to possibly remove code duplication.
            var folder = Path.GetDirectoryName(source);
            var fileName = Path.GetFileName(source);
            var copyFileName = $"Copy of {fileName}";
            var destination = _fileSystem.PathCombine(
                _fileSystem.PathCombine(new NPath(folder), new NPath(state.Target.Raw)),
                new NPath(copyFileName));

            while (_fileSystem.FileExists(destination))
            {
                fileName = Path.GetFileName(destination.Raw);
                copyFileName = $"Copy of {fileName}";
                destination = _fileSystem.PathCombine(
                    _fileSystem.PathCombine(new NPath(folder), new NPath(state.Target.Raw)),
                    new NPath(copyFileName));
            }

            _fileSystem.CopyFile(new NPath(source), destination, true);
            var fileResult = new
            {
                id = destination.Raw,
                value = copyFileName
            };

            return fileResult;
        }

        public object GetResult()
        {
            return Result.Result;
        }

        public CopyResult Result { get; private set; }
    }
}