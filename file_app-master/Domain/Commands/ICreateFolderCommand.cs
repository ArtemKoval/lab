namespace Domain.Commands
{
    public interface ICreateFolderCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}