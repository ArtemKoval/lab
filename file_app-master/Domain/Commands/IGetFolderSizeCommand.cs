namespace Domain.Commands
{
    public interface IGetFolderSizeCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}