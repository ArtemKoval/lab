using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Domain.Commands;

namespace Domain.FileSystem
{
    public interface IFileSystemService
    {
        Task<List<TreeDTO>> GetStructureAsync();
        Task<object> UploadFileAsync(UploadFileState state);
        Task<object> RemoveAsync(RemoveState state);
        Task<object> RenameAsync(RenameState state);
        Task<object> CreateFolderAsync(CreateFolderState state);
        Task<object> CopyAsync(CopyState state);
        Task<Stream> DownloadFileAsync(DownloadFileState state);
    }
}