namespace Domain.Commands
{
    public interface IDownloadFileCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}