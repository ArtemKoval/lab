namespace Domain.Commands
{
    public interface IRenameCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}