namespace Domain.Commands
{
    public interface IResult
    {
        bool Success { get; }
        object Result { get; }
    }
}