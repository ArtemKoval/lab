namespace Domain.Commands
{
    public class CreateFolderResult : IResult
    {
        public CreateFolderResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}