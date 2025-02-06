using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Domain.Commands;
using NFS;

namespace Domain.FileSystem
{
    public class FileSystemService : IFileSystemService
    {
        private readonly IFileSystem _fileSystem;
        private readonly IGetFolderSizeCommand<GetFolderSizeResult, long, GetFolderSizeState> _getFolderSizeCommand;
        private readonly IUploadFileCommand<UploadFileResult, object, UploadFileState> _uploadFileCommand;
        private readonly IRemoveCommand<RemoveResult, bool, RemoveState> _removeCommand;
        private readonly IDownloadFileCommand<DownloadFileResult, Stream, DownloadFileState> _downloadFileCommand;
        private readonly IRenameCommand<RenameResult, object, RenameState> _renameCommand;
        private readonly ICreateFolderCommand<CreateFolderResult, object, CreateFolderState> _createFolderCommand;
        private readonly ICopyCommand<CopyResult, object, CopyState> _copyCommand;

        public FileSystemService(
            IFileSystem fileSystem,
            IGetFolderSizeCommand<GetFolderSizeResult, long, GetFolderSizeState> getFolderSizeCommand,
            IUploadFileCommand<UploadFileResult, object, UploadFileState> uploadFileCommand,
            IRemoveCommand<RemoveResult, bool, RemoveState> removeCommand,
            IDownloadFileCommand<DownloadFileResult, Stream, DownloadFileState> downloadFileCommand,
            IRenameCommand<RenameResult, object, RenameState> renameCommand,
            ICreateFolderCommand<CreateFolderResult, object, CreateFolderState> createFolderCommand,
            ICopyCommand<CopyResult, object, CopyState> copyCommand
        )
        {
            _fileSystem = fileSystem;
            _getFolderSizeCommand = getFolderSizeCommand;
            _uploadFileCommand = uploadFileCommand;
            _removeCommand = removeCommand;
            _downloadFileCommand = downloadFileCommand;
            _renameCommand = renameCommand;
            _createFolderCommand = createFolderCommand;
            _copyCommand = copyCommand;
        }

        private static long TimeToMilliseconds(DateTime time)
        {
            var milliseconds = new DateTimeOffset(time)
                .ToUnixTimeSeconds();

            return milliseconds;
        }

        private IEnumerable<TreeDTO> GetFileStructure(NPath node)
        {
            var files = _fileSystem
                .EnumerateFileEntries(node);

            // TODO: move to the factory

            return files.Select(file => new TreeDTO
                {
                    Id = file.FullName,
                    Date = TimeToMilliseconds(
                        _fileSystem
                            .GetLastWriteTime(new NPath(file.ToString()))),
                    Size = file.Length,
                    Type = NodeType.File,
                    Value = file.Name
                })
                .OrderBy(f => f.Value)
                .ToList();
        }

        private List<TreeDTO> GetFolderStructure(NPath node)
        {
            var directories = _fileSystem
                .EnumerateDirectories(node);

            var tree = new List<TreeDTO>();

            foreach (var dir in directories)
            {
                var data = GetFolderStructure(new NPath(dir.FullName));
                data.AddRange(GetFileStructure(new NPath(dir.FullName)));
                data = data
                    .OrderBy(f => f.Value)
                    .ToList();

                _getFolderSizeCommand
                    .Execute(
                        new GetFolderSizeState(new NPath(dir.FullName))
                    );

                var nodeDTO = new TreeDTO
                {
                    Id = dir.FullName,
                    Date = TimeToMilliseconds(
                        _fileSystem
                            .GetLastWriteTime(dir.Path)),
                    Size = _getFolderSizeCommand
                        .GetResult(),
                    Type = NodeType.Folder,
                    Value = new DirectoryInfo(dir.FullName).Name,
                    Data = data
                };

                tree.Add(nodeDTO);
            }

            return tree
                .OrderBy(n => n.Value)
                .ToList();
        }

        public async Task<List<TreeDTO>> GetStructureAsync()
        {
            return await Task.Run(() => GetFolderStructure(new NPath(System.IO.Directory.GetCurrentDirectory())));
        }

        public async Task<object> UploadFileAsync(UploadFileState state)
        {
            await _uploadFileCommand.ExecuteAsync(state);

            return _uploadFileCommand.GetResult();
        }

        public async Task<object> RemoveAsync(RemoveState state)
        {
            var result = await _removeCommand.ExecuteAsync(state);

            return result;
        }

        public async Task<object> RenameAsync(RenameState state)
        {
            await _renameCommand.ExecuteAsync(state);

            return _renameCommand.GetResult();
        }

        public async Task<object> CreateFolderAsync(CreateFolderState state)
        {
            await _createFolderCommand.ExecuteAsync(state);

            return _createFolderCommand.GetResult();
        }

        public async Task<object> CopyAsync(CopyState state)
        {
            await _copyCommand.ExecuteAsync(state);

            return _copyCommand.GetResult();
        }

        public async Task<Stream> DownloadFileAsync(DownloadFileState state)
        {
            await _downloadFileCommand.ExecuteAsync(state);

            return _downloadFileCommand.GetResult();
        }
    }
}