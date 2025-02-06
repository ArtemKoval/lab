namespace Domain.Commands
{
    public class GetFolderSizeResult: IResult
    {
        public GetFolderSizeResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}