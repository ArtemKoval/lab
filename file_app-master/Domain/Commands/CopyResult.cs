namespace Domain.Commands
{
    public class CopyResult: IResult
    {
        public CopyResult(bool success,
            object result)
        {
            Success = success;
            Result = result;
        }

        public bool Success { get; }
        public object Result { get; }
    }
}