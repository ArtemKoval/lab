namespace Domain.Commands
{
    public class RemoveResult : IResult
    {
        public RemoveResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}