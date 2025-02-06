namespace Domain.Commands
{
    public class RenameResult : IResult
    {
        public RenameResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}