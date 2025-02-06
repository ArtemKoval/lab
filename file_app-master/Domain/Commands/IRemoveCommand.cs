namespace Domain.Commands
{
    public interface IRemoveCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}