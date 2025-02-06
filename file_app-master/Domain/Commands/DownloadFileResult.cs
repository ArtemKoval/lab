namespace Domain.Commands
{
    public class DownloadFileResult: IResult
    {
        public DownloadFileResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}