using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace Domain.Commands
{
    public class GetFolderSizeCommand
        : IGetFolderSizeCommand<GetFolderSizeResult, long, GetFolderSizeState>
    {
        private static long GetDirectorySize(DirectoryInfo directoryInfo)
        {
            var fileInfos = directoryInfo
                .GetFiles();
            var size = fileInfos
                .Sum(fi => fi.Length);

            var directoryInfos = directoryInfo
                .GetDirectories();
            size += directoryInfos
                .Sum(di => GetDirectorySize(di));

            return size;
        }

        public async Task<GetFolderSizeResult> ExecuteAsync(GetFolderSizeState state)
        {
            return await Task.Run(() => Execute(state));
        }

        public GetFolderSizeResult Execute(GetFolderSizeState state)
        {
            long size = 0;

            try
            {
                var directoryInfo = new DirectoryInfo(state.Target.Raw);

                size += GetDirectorySize(directoryInfo);

                Result = new GetFolderSizeResult(true, size);
            }
            catch (Exception e)
            {
                Console.WriteLine(e);

                Result = new GetFolderSizeResult(true, 0L);
            }

            return Result;
        }

        public long GetResult()
        {
            return (long) Result.Result;
        }

        public GetFolderSizeResult Result { get; private set; }
    }
}