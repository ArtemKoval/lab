namespace Domain.Commands
{
    public class UploadFileResult : IResult
    {
        public UploadFileResult(bool success,
         object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}